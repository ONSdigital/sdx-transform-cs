from transform import app

from flask import request, make_response, send_file
from transformers import PCKTransformer, PDFTransformer, ImageTransformer, CSTransformer
from jinja2 import Environment, PackageLoader

import os
import dateutil.parser
import json

env = Environment(loader=PackageLoader('transform', 'templates'))


def get_survey(survey_response):
    form_id = survey_response['collection']['instrument_id']

    with open("./surveys/%s.%s.json" % (survey_response['survey_id'], form_id)) as json_file:
        return json.load(json_file)


@app.route('/pck', methods=['POST'])
@app.route('/pck/<batch_number>', methods=['POST'])
def render_pck(batch_number=False):
    response = request.get_json(force=True)
    template = env.get_template('pck.tmpl')
    survey = get_survey(response)

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

    return template.render(response=response, survey=survey)


@app.route('/pdf', methods=['POST'])
def render_pdf():
    survey_response = request.get_json(force=True)

    survey = get_survey(survey_response)

    pdf = PDFTransformer(survey, survey_response)
    rendered_pdf = pdf.render()

    response = make_response(rendered_pdf)
    response.mimetype = 'application/pdf'

    return response


@app.route('/images', methods=['POST'])
def render_images():
    survey_response = request.get_json(force=True)

    survey = get_survey(survey_response)

    itransformer = ImageTransformer(survey, survey_response)

    itransformer.create_pdf()
    itransformer.create_image_sequence()
    itransformer.create_image_index()
    zipfile = itransformer.create_zip()
    itransformer.cleanup()

    return send_file(zipfile, mimetype='application/zip')


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

    ctransformer = CSTransformer(survey, survey_response, batch_number, sequence_no)

    ctransformer.create_formats()
    ctransformer.prepare_archive()
    zipfile = ctransformer.create_zip()
    ctransformer.cleanup()

    return send_file(zipfile, mimetype='application/zip')
