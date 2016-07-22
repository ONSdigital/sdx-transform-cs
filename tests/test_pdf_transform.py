import unittest
import json
from transform.views.test_views import test_message
from transform.transformers import PDFTransformer


class TestPDFTransformer(unittest.TestCase):
    def test_localised_time(self):
        with open("./transform/surveys/023.0203.json") as survey:
            response = json.loads(test_message)
            pdf_transformer = PDFTransformer(survey, response)

            expected_date = "Sat 12 Mar 10:39:40 2016"
            actual_date = pdf_transformer.get_localised_date(response['submitted_at'])

            self.assertEqual(expected_date, actual_date)

            expected_date = "Sat 12 Mar 02:39:40 2016"
            actual_date = pdf_transformer.get_localised_date(response['submitted_at'], timezone='US/Pacific')

            self.assertEqual(expected_date, actual_date)

            expected_date = "Sat 12 Mar 18:39:40 2016"
            actual_date = pdf_transformer.get_localised_date(response['submitted_at'], timezone='Asia/Shanghai')

            self.assertEqual(expected_date, actual_date)

            expected_date = "Sat 12 Mar 13:39:40 2016"
            actual_date = pdf_transformer.get_localised_date(response['submitted_at'], timezone='Europe/Moscow')

            self.assertEqual(expected_date, actual_date)
