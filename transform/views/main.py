import json
import logging
import os.path

from flask import request, send_file, jsonify
from jinja2 import Environment, PackageLoader
from structlog import wrap_logger
from transform.views.logger_config import logger_initial_config

from transform import app, settings
from transform.transformers import ImageTransformer
from transform.transformers.common_software import CSTransformer, MBSTransformer, MWSSTransformer, PCKTransformer
from transform.transformers.cora import UKISTransformer
from transform.transformers.cord import EcommerceTransformer

cord_surveys = ["187"]
cora_surveys = ["144"]
env = Environment(loader=PackageLoader('transform', 'templates'))

logger_initial_config(service_name='sdx-transform-cs',
                      log_level=settings.LOGGING_LEVEL)
logger = wrap_logger(logging.getLogger(__name__))


@app.errorhandler(400)
def errorhandler_400(e):
    return client_error(repr(e))


def client_error(error=None):
    logger.error("Client error", error=error)
    message = {
        'status': 400,
        'message': error,
        'uri': request.url,
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@app.errorhandler(500)
def server_error(error=None):
    logger.error("Server error", error=repr(error))
    message = {
        'status': 500,
        'message': "Internal server error: " + repr(error),
    }
    resp = jsonify(message)
    resp.status_code = 500

    return resp


def get_survey(survey_response):
    try:
        form_id = survey_response['collection']['instrument_id']
        survey_id = survey_response.get("survey_id", "N/A")
        tx_id = survey_response.get("tx_id", "N/A")
        logger.info("Loading survey", survey="{0}-{1}.json".format(survey_id, form_id), tx_id=tx_id)

        fp = os.path.join(
            ".", "transform", "surveys",
            "{0}.{1}.json".format(survey_response['survey_id'], form_id)
        )
        logger.info("Opening file", file=fp, tx_id=tx_id)
        with open(fp, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    except (IOError, UnicodeDecodeError) as e:
        logger.exception("Error opening file", file=fp, tx_id=tx_id, error=e)
        return False


@app.route('/pck', methods=['POST'])
@app.route('/pck/<batch_number>', methods=['POST'])
def render_pck(batch_number=False):
    """
    This endpoint will return the pck file from the supplied survey response.  Note this will
    only return the pck file and none of the other files that are usually generated from a submission.
    This endpoint can be called with an optional batch_number.  Batch numbers are only
    used for common-software surveys.
    """
    response = request.get_json(force=True)
    survey = get_survey(response)

    if not survey:
        return client_error("PCK:Unsupported survey/instrument id")

    survey_id = survey.get("survey_id")
    bound_logger = logger.bind(
        survey_id=survey_id,
        tx_id=response.get("tx_id"),
        form_id=response['collection']['instrument_id']
    )

    if survey_id in cord_surveys:
        bound_logger.info("PCK:CORD survey detected")
        if batch_number:
            return client_error("PCK:CORD surveys don't support batch numbers")

        transformer = EcommerceTransformer(response)
        transformed_data = transformer.transform()
        bound_logger.info("PCK:SUCCESS")
        return transformer.create_pck(transformed_data)

    if survey_id in cora_surveys:
        bound_logger.info("PCK:CORA survey detected")
        if batch_number:
            return client_error("PCK:CORA surveys don't support batch numbers")

        transformer = UKISTransformer(response)
        transformed_data = transformer.transform()
        bound_logger.info("PCK:SUCCESS")

        return transformer.create_pck(transformed_data)

    template = env.get_template('pck.tmpl')
    if batch_number:
        batch_number = int(batch_number)

    pck_transformer = PCKTransformer(survey, response)
    answers = pck_transformer.derive_answers()
    cs_form_id = pck_transformer.get_cs_form_id()
    sub_date_str = pck_transformer.get_subdate_str()

    bound_logger.info("PCK:SUCCESS")

    return template.render(response=response, submission_date=sub_date_str,
                           batch_number=batch_number, form_id=cs_form_id,
                           answers=answers)


@app.route('/idbr', methods=['POST'])
def render_idbr():
    response = request.get_json(force=True)
    template = env.get_template('idbr.tmpl')

    logger.info("IDBR:SUCCESS")

    return template.render(response=response)


@app.route('/images', methods=['POST'])
def render_images():

    survey_response = request.get_json(force=True)

    survey = get_survey(survey_response)

    if not survey:
        return client_error("IMAGES:Unsupported survey/instrument id")

    transformer = ImageTransformer(logger, survey, survey_response)

    try:
        zipfile = transformer.get_zipped_images()
    except IOError as e:
        return client_error("IMAGES:Could not create zip buffer: {0}".format(repr(e)))
    except Exception as e:
        logger.exception("IMAGES: Error {0}".format(repr(e)))
        return server_error(e)
    logger.info("IMAGES:SUCCESS")

    return send_file(zipfile.in_memory_zip, mimetype='application/zip', add_etags=False)


@app.route('/common-software', methods=['POST'])
@app.route('/common-software/<sequence_no>', methods=['POST'])
@app.route('/common-software/<sequence_no>/<batch_number>', methods=['POST'])
def common_software(sequence_no=1000, batch_number=0):
    survey_response = request.get_json(force=True)

    if batch_number:
        batch_number = int(batch_number)

    if sequence_no:
        sequence_no = int(sequence_no)

    survey = get_survey(survey_response)
    if not survey:
        return client_error("CS:Unsupported survey/instrument id")

    survey_id = survey_response.get("survey_id")
    try:
        if survey_id == "009":
            transformer = MBSTransformer(survey_response, sequence_no)
        elif survey_id == "134":
            transformer = MWSSTransformer(survey_response, sequence_no, log=logger)
        else:
            transformer = CSTransformer(logger, survey, survey_response, batch_number, sequence_no)

        transformer.create_zip()

    except Exception as e:
        tx_id = survey_response.get("tx_id")
        logger.exception("CS:could not create files for survey", survey_id=survey_id, tx_id=tx_id)
        return server_error(e)

    logger.info("CS:SUCCESS")

    return send_file(transformer.image_transformer.get_zip(), mimetype='application/zip', add_etags=False)


@app.route('/cora', methods=['POST'])
@app.route('/cora/<sequence_no>', methods=['POST'])
def cora(sequence_no=1000):
    survey_response = request.get_json(force=True)

    if sequence_no:
        sequence_no = int(sequence_no)

    survey = get_survey(survey_response)
    if not survey:
        return client_error("CORA:Unsupported survey/instrument id")

    survey_id = survey_response.get("survey_id")
    try:
        if survey_id == "144":
            transformer = UKISTransformer(survey_response, sequence_no)
            transformer.create_zip()
        else:
            return client_error("CORA survey with survey id {} is not supported".format(survey_id))

    except Exception as e:
        tx_id = survey_response.get("tx_id")
        logger.exception("CORA:could not create files for survey", survey_id=survey_id, tx_id=tx_id)
        return server_error(e)

    logger.info("CORA:SUCCESS")

    return send_file(transformer.image_transformer.get_zip(), mimetype='application/zip', add_etags=False)


@app.route('/cord', methods=['POST'])
@app.route('/cord/<sequence_no>', methods=['POST'])
def cord(sequence_no=1000):
    survey_response = request.get_json(force=True)

    if sequence_no:
        sequence_no = int(sequence_no)

    survey = get_survey(survey_response)
    if not survey:
        return client_error("CS:Unsupported survey/instrument id")

    survey_id = survey_response.get("survey_id")
    try:
        if survey_id == "187":
            transformer = EcommerceTransformer(survey_response, sequence_no)
            transformer.create_zip()
        else:
            return client_error("CORD survey with survey id {} is not supported".format(survey_id))

    except Exception as e:
        tx_id = survey_response.get("tx_id")
        logger.exception("CORD:could not create files for survey", survey_id=survey_id, tx_id=tx_id)
        return server_error(e)

    logger.info("CORD:SUCCESS")

    return send_file(transformer.image_transformer.get_zip(), mimetype='application/zip', add_etags=False)


@app.route('/info', methods=['GET'])
@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    """A simple endpoint that reports the health of the application"""
    return jsonify({'status': 'OK'})
