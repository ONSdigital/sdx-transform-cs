import json
import logging
import os.path

from flask import request, make_response, send_file, jsonify
from jinja2 import Environment, PackageLoader
from structlog import wrap_logger
from transform.views.logger_config import logger_initial_config

from transform import app
from transform import settings
from transform.transformers import CSTransformer, ImageTransformer, MWSSTransformer, PCKTransformer, PDFTransformer

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
    response = request.get_json(force=True)
    template = env.get_template('pck.tmpl')
    survey = get_survey(response)

    if not survey:
        return client_error("PCK:Unsupported survey/instrument id")

    if batch_number:
        batch_number = int(batch_number)

    pck_transformer = PCKTransformer(survey, response)
    answers = pck_transformer.derive_answers()
    cs_form_id = pck_transformer.get_cs_form_id()
    sub_date_str = pck_transformer.get_subdate_str()

    logger.info("PCK:SUCCESS")

    return template.render(response=response, submission_date=sub_date_str,
                           batch_number=batch_number, form_id=cs_form_id,
                           answers=answers)


@app.route('/idbr', methods=['POST'])
def render_idbr():
    response = request.get_json(force=True)
    template = env.get_template('idbr.tmpl')

    logger.info("IDBR:SUCCESS")

    return template.render(response=response)


@app.route('/html', methods=['POST'])
def render_html():
    response = request.get_json(force=True)
    template = env.get_template('html.tmpl')

    survey = get_survey(response)

    if not survey:
        return client_error("HTML:Unsupported survey/instrument id")

    logger.info("HTML:SUCCESS")

    return template.render(response=response, survey=survey)


@app.route('/pdf', methods=['POST'])
def render_pdf():
    survey_response = request.get_json(force=True)

    survey = get_survey(survey_response)

    if not survey:
        return client_error("PDF:Unsupported survey/instrument id")

    try:
        pdf = PDFTransformer(survey, survey_response)
        rendered_pdf = pdf.render()

    except IOError as e:
        return client_error("PDF:Could not render pdf buffer: {0}".format(repr(e)))
    except Exception as e:
        survey_id = survey_response.get("survey_id")
        tx_id = survey_response.get("tx_id")
        logger.exception("PDF:Generation failed", survey_id=survey_id, tx_id=tx_id)
        raise e

    response = make_response(rendered_pdf)
    response.mimetype = 'application/pdf'

    logger.info("PDF:SUCCESS")

    return response


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
        if survey_id == "134":
            transformer = MWSSTransformer(survey_response, sequence_no, log=logger)
        else:
            transformer = CSTransformer(logger, survey, survey_response, batch_number, sequence_no)

        transformer.create_zip()

    except Exception as e:
        tx_id = survey_response.get("tx_id")
        logger.exception("CS:could not create files for survey", survey_id=survey_id, tx_id=tx_id)
        return server_error(e)

    logger.info("CS:SUCCESS")

    return send_file(transformer.get_zip(), mimetype='application/zip', add_etags=False)


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'OK'})
