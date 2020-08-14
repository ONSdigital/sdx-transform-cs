import json
import unittest

from transform.transformers import PDFTransformer


class TestPDFTransformer(unittest.TestCase):
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
            "24": "74.125",
            "25": "50",
            "26": "100",
            "21": "60000",
            "27": "7400",
            "146": "some comment"
        }
    }'''

    def test_localised_time(self):
        with open("./transform/surveys/134.0005.json") as survey:
            response = json.loads(self.test_message)
            pdf_transformer = PDFTransformer(survey, response)

            expected_date = "12 March 2016 10:39:40"
            actual_date = pdf_transformer.get_localised_date(response['submitted_at'])

            self.assertEqual(expected_date, actual_date)

            expected_date = "12 March 2016 02:39:40"
            actual_date = pdf_transformer.get_localised_date(response['submitted_at'], timezone='US/Pacific')

            self.assertEqual(expected_date, actual_date)

            expected_date = "12 March 2016 18:39:40"
            actual_date = pdf_transformer.get_localised_date(response['submitted_at'], timezone='Asia/Shanghai')

            self.assertEqual(expected_date, actual_date)

            expected_date = "12 March 2016 13:39:40"
            actual_date = pdf_transformer.get_localised_date(response['submitted_at'], timezone='Europe/Moscow')

            self.assertEqual(expected_date, actual_date)
