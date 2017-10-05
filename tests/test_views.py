from jinja2 import Environment, PackageLoader

from flask import send_file
import logging
from structlog import wrap_logger
import json
import os.path
import unittest

from transform import app
from transform import settings
from sdx.common.transformer import ImageTransformer, PDFTransformer

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

        itransformer = ImageTransformer(logger, settings, survey, survey_response)

        path = PDFTransformer.render_to_file(survey, survey_response)
        locn = os.path.dirname(path)
        images = list(itransformer.create_image_sequence(path))
        index = itransformer.create_image_index(images)
        zipfile = itransformer.create_zip(images, index)

        itransformer.cleanup(locn)

        return send_file(zipfile, mimetype='application/zip')


@app.route('/html-test', methods=['GET'])
def html_test():

    response = json.loads(test_message)
    template = env.get_template('html.tmpl')
    form_id = response['collection']['instrument_id']

    with open("./transform/surveys/%s.%s.json" % (response['survey_id'], form_id)) as json_file:
        survey = json.load(json_file)
        return template.render(response=response, survey=survey)


class TestCSTransformService(unittest.TestCase):

    transform_cs_endpoint = "/common-software"

    def setUp(self):

        # creates a test client
        self.app = app.test_client()

        # propagate the exceptions to the test client
        self.app.testing = True

    def test_invalid_data(self):
        r = self.app.post(self.transform_cs_endpoint, data="rubbish")

        self.assertEqual(r.status_code, 400)
