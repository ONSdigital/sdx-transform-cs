import json
import logging

from flask import make_response, send_file
from jinja2 import Environment, PackageLoader
from structlog import wrap_logger

from transform import app
from transform.transformers import PDFTransformer, CSTransformer
from transform.transformers.image_transformer import ImageTransformer

logger = wrap_logger(logging.getLogger(__name__))

env = Environment(loader=PackageLoader('transform', 'templates'))

test_message = '''{
   "type": "uk.gov.ons.edc.eq:surveyresponse",
   "origin": "uk.gov.ons.edc.eq",
   "survey_id": "023",
   "version": "0.0.1",
   "collection": {
     "exercise_sid": "hfjdskf",
     "instrument_id": "0203",
     "period": "0216"
   },
   "submitted_at": "2016-03-12T10:39:40Z",
   "metadata": {
     "user_id": "789473423",
     "ru_ref": "12345678901A"
   },
   "data": {
     "11": "01/04/2016",
     "12": "31/10/2016",
     "20": "1800000",
     "51": "84",
     "52": "10",
     "53": "73",
     "54": "24",
     "50": "205",
     "22": "705000",
     "23": "900",
     "24": "74",
     "25": "50",
     "26": "100",
     "21": "60000",
     "27": "7400",
     "146": "some comment"
   }
}'''


@app.route('/images-test', methods=['GET'])
def images_test():
    survey_response = json.loads(test_message)
    form_id = survey_response['collection']['instrument_id']

    with open("./transform/surveys/%s.%s.json" % (survey_response['survey_id'], form_id)) as json_file:
        survey = json.load(json_file)

        itransformer = ImageTransformer(logger, survey, survey_response)
        zipfile = itransformer.get_zipped_images()

        return send_file(zipfile.in_memory_zip, mimetype='application/zip')


@app.route('/pdf-test', methods=['GET'])
def pdf_test():
    survey_response = json.loads(test_message)
    form_id = survey_response['collection']['instrument_id']

    with open("./transform/surveys/%s.%s.json" % (survey_response['survey_id'], form_id)) as json_file:
        survey = json.load(json_file)

        pdf = PDFTransformer(survey, survey_response)
        rendered_pdf = pdf.render()

        response = make_response(rendered_pdf)
        response.mimetype = 'application/pdf'

        return response


@app.route('/html-test', methods=['GET'])
def html_test():

    response = json.loads(test_message)
    template = env.get_template('html.tmpl')
    form_id = response['collection']['instrument_id']

    with open("./transform/surveys/%s.%s.json" % (response['survey_id'], form_id)) as json_file:
        survey = json.load(json_file)
        return template.render(response=response, survey=survey)


@app.route('/cs-test', methods=['GET'])
def cs_test():
    survey_response = json.loads(test_message)
    form_id = survey_response['collection']['instrument_id']

    with open("./transform/surveys/%s.%s.json" % (survey_response['survey_id'], form_id)) as json_file:
        survey = json.load(json_file)

        ctransformer = CSTransformer(logger, survey, survey_response)
        ctransformer.create_zip()

        return send_file(ctransformer.image_transformer.zip.in_memory_zip, mimetype='application/zip')
