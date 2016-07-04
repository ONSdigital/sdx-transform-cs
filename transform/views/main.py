from transform import app

from flask import request, make_response, send_file, jsonify
from transformers import PCKTransformer, PDFTransformer, ImageTransformer, CSTransformer
from jinja2 import Environment, PackageLoader

import json

env = Environment(loader=PackageLoader('transform', 'templates'))


@app.errorhandler(400)
def known_error(error=None):
    app.logger.error("FAILURE:%s", repr(error))
    message = {
        'status': 400,
        'message': repr(error),
        'uri': request.url,
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@app.errorhandler(500)
def unknown_error(error=None):
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

        with open("./surveys/%s.%s.json" % (survey_response['survey_id'], form_id)) as json_file:
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
        return known_error("PCK:Unsupported survey/instrument id")

    if batch_number:
        batch_number = int(batch_number)

    pck_transformer = PCKTransformer(survey, response)
    answers = pck_transformer.derive_answers()
    cs_form_id = pck_transformer.get_cs_form_id()
    sub_date_str = pck_transformer.get_subdate_str()

    return template.render(response=response, submission_date=sub_date_str,
                           batch_number=batch_number, form_id=cs_form_id,
                           answers=answers)


@app.route('/idbr', methods=['POST'])
def render_idbr():
    response = request.get_json(force=True)
    template = env.get_template('idbr.tmpl')

    return template.render(response=response)


@app.route('/html', methods=['POST'])
def render_html():
    response = request.get_json(force=True)
    template = env.get_template('html.tmpl')

    survey = get_survey(response)

    if not survey:
        return known_error("HTML:Unsupported survey/instrument id")

    app.logger.info("HTML:SUCCESS")

    return template.render(response=response, survey=survey)


@app.route('/pdf', methods=['POST'])
def render_pdf():
    survey_response = request.get_json(force=True)

    survey = get_survey(survey_response)

    if not survey:
        return known_error("PDF:Unsupported survey/instrument id")

    try:
        pdf = PDFTransformer(survey, survey_response)
        rendered_pdf = pdf.render()

    except IOError as e:
        return known_error("PDF:Could not render pdf buffer: %s" % repr(e))

    response = make_response(rendered_pdf)
    response.mimetype = 'application/pdf'

    app.logger.info("PDF:SUCCESS")

    return response


@app.route('/images', methods=['POST'])
def render_images():
    survey_response = request.get_json(force=True)

    survey = get_survey(survey_response)

    if not survey:
        return known_error("IMAGES:Unsupported survey/instrument id")

    itransformer = ImageTransformer(survey, survey_response)

    try:
        itransformer.create_pdf()
        itransformer.create_image_sequence()
        itransformer.create_image_index()
        zipfile = itransformer.create_zip()
        itransformer.cleanup()
    except IOError as e:
        return known_error("IMAGES:Could not create zip buffer: %s" % repr(e))

    app.logger.info("IMAGES:SUCCESS")

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
        return known_error("CS:Unsupported survey/instrument id")

    ctransformer = CSTransformer(survey, survey_response, batch_number, sequence_no)

    try:
        ctransformer.create_formats()
        ctransformer.prepare_archive()
        zipfile = ctransformer.create_zip()
        ctransformer.cleanup()
    except IOError as e:
        return known_error("CS:Could not create zip buffer: %s" % repr(e))

    app.logger.info("CS:SUCCESS")

    return send_file(zipfile, mimetype='application/zip', add_etags=False)
