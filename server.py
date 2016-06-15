import settings
import json
from transform import app
import logging
import logging.handlers
from io import BytesIO
from jinja2 import Environment, PackageLoader
from flask import Flask, request, make_response, send_file
from transformers import derive_answers, form_ids, PDFTransformer, ImageTransformer

import dateutil.parser

env = Environment(loader=PackageLoader('transform', 'templates'))

@app.route('/pck', methods=['POST'])
@app.route('/pck/<batch_number>', methods=['POST'])
def render_pck(batch_number=30001):
    batch_number = int(batch_number)
    response = request.get_json(force=True)
    template = env.get_template('pck.tmpl')

    form_id = response['collection']['instrument_id']

    instrument_id = response['collection']['instrument_id']

    submission_date = dateutil.parser.parse(response['submitted_at'])
    submission_date_str = submission_date.strftime("%d/%m/%y")

    cs_form_id = form_ids[instrument_id]

    data = response['data'] if 'data' in response else {}

    with open("./surveys/%s.%s.json" % (response['survey_id'], form_id)) as json_file:
        survey = json.load(json_file)

        answers = derive_answers(survey, data)

        return template.render(response=response, submission_date=submission_date_str,
                               batch_number=batch_number, form_id=cs_form_id,
                               answers=answers, write_batch_header=app.config['WRITE_BATCH_HEADER'])


@app.route('/idbr', methods=['POST'])
def render_idbr():
    response = request.get_json(force=True)
    template = env.get_template('idbr.tmpl')

    return template.render(response=response)


@app.route('/html', methods=['POST'])
def render_html():
    response = request.get_json(force=True)
    template = env.get_template('html.tmpl')

    form_id = response['collection']['instrument_id']

    with open("./surveys/%s.%s.json" % (response['survey_id'], form_id)) as json_file:
        survey = json.load(json_file)
        return template.render(response=response, survey=survey)


@app.route('/pdf', methods=['POST'])
def render_pdf():
    survey_response = request.get_json(force=True)

    form_id = survey_response['collection']['instrument_id']

    with open("./surveys/%s.%s.json" % (survey_response['survey_id'], form_id)) as json_file:
        survey = json.load(json_file)
        buffer = BytesIO()
        pdf = PDFTransformer(buffer, survey, survey_response)
        rendered_pdf = pdf.render()

        response = make_response(rendered_pdf)
        # response.headers['Content-Disposition'] = "attachment; filename='response.pdf"
        response.mimetype = 'application/pdf'

        return response


@app.route('/images', methods=['POST'])
def render_images():
    survey_response = request.get_json(force=True)
    form_id = survey_response['collection']['instrument_id']

    with open("./surveys/%s.%s.json" % (survey_response['survey_id'], form_id)) as json_file:
        survey = json.load(json_file)

        itransformer = ImageTransformer(survey, survey_response)

        itransformer.create_pdf()
        itransformer.create_image_sequence()
        itransformer.create_image_index()
        zipname = itransformer.create_zip()

        itransformer.cleanup()

        return send_file(os.path.join(itransformer.path, zipname), mimetype='application/zip')

if __name__ == '__main__':
    # Startup
    logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
    app.run(debug=True, host='0.0.0.0')

