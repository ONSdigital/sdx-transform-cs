import json
import logging
import os.path

from flask import request, make_response, send_file, jsonify
from jinja2 import Environment, PackageLoader
from structlog import wrap_logger

from transform import app
from transform import settings
from transform.transformers import ImageTransformer, CSTransformer
from transform.transformers import MWSSTransformer
from transform.transformers import PCKTransformer, PDFTransformer

env = Environment(loader=PackageLoader('transform', 'templates'))

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
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

        fp = os.path.join(
            ".", "transform", "surveys",
            "{0}.{1}.json".format(survey_response['survey_id'], form_id)
        )
        with open(fp, 'r') as json_file:
            return json.load(json_file)
    except IOError:
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

    itransformer = ImageTransformer(logger, survey, survey_response)

    try:
        path = itransformer.create_pdf(survey, survey_response)
        images = list(itransformer.create_image_sequence(path))
        index = itransformer.create_image_index(images)
        zipfile = itransformer.create_zip(images, index)
        itransformer.cleanup(os.path.dirname(path))
    except IOError as e:
        return client_error("IMAGES:Could not create zip buffer: {0}".format(repr(e)))

    logger.info("IMAGES:SUCCESS")

    return send_file(zipfile, mimetype='application/zip', add_etags=False)


@app.route('/common-software', methods=['POST'])
@app.route('/common-software/<sequence_no>', methods=['POST'])
@app.route('/common-software/<sequence_no>/<batch_number>', methods=['POST'])
def common_software(sequence_no=1000, batch_number=False):
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
            tfr = MWSSTransformer(survey_response, sequence_no, log=logger)
            zipfile = tfr.pack()
        else:
            ctransformer = CSTransformer(
                logger, survey, survey_response, batch_number, sequence_no)

            ctransformer.create_formats()
            ctransformer.prepare_archive()
            zipfile = ctransformer.create_zip()
            try:
                ctransformer.cleanup()
            except IOError as e:
                return client_error("CS:Could not create zip buffer: {0}".format(repr(e)))
    except Exception as e:
        return server_error(e)

    logger.info("CS:SUCCESS")

    return send_file(zipfile, mimetype='application/zip', add_etags=False)


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'OK'})
