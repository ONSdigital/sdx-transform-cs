import io
import json
import unittest
import zipfile

from transform import app
from unittest.mock import patch


class TestCSTransformService(unittest.TestCase):

    transform_cs_endpoint = "/common-software"
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

    def setUp(self):

        # creates a test client
        self.app = app.test_client()

        # propagate the exceptions to the test client
        self.app.testing = True

    def get_zip_file_contents(self, endpoint, msg_data=test_message):
        response = self.app.post(endpoint, data=msg_data)
        return io.BytesIO(response.data)

    def get_zip_list(self, endpoint):
        zip_contents = self.get_zip_file_contents(endpoint)
        z = zipfile.ZipFile(zip_contents)
        z.close()

        return z.namelist()

    @patch('transform.transformers.ImageTransformer._get_image_sequence_list', return_value=[13, 14])
    def test_creates_cs_defaults(self, mock_sequence_no):  # pylint: disable=unused-argument

        ziplist = self.get_zip_list(self.transform_cs_endpoint)

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/023_1000',
            'EDC_QReceipts/REC1203_1000.DAT',
            'EDC_QImages/Images/S000000013.JPG',
            'EDC_QImages/Images/S000000014.JPG',
            'EDC_QImages/Index/EDC_023_20160312_1000.csv',
            'EDC_QJson/023_1000.json'
        ]

        self.assertEqual(expected, ziplist)

    @patch('transform.transformers.ImageTransformer._get_image_sequence_list', return_value=[1985, 1986])
    def test_creates_cs_sequence(self, mock_sequence_no):  # pylint: disable=unused-argument

        ziplist = self.get_zip_list(self.transform_cs_endpoint + "/2345")

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/023_2345',
            'EDC_QReceipts/REC1203_2345.DAT',
            'EDC_QImages/Images/S000001985.JPG',
            'EDC_QImages/Images/S000001986.JPG',
            'EDC_QImages/Index/EDC_023_20160312_2345.csv',
            'EDC_QJson/023_2345.json'
        ]

        self.assertEqual(expected, ziplist)

        ziplist = self.get_zip_list(self.transform_cs_endpoint + "/999")

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/023_0999',
            'EDC_QReceipts/REC1203_0999.DAT',
            'EDC_QImages/Images/S000001985.JPG',
            'EDC_QImages/Images/S000001986.JPG',
            'EDC_QImages/Index/EDC_023_20160312_0999.csv',
            'EDC_QJson/023_0999.json'
        ]

        self.assertEqual(expected, ziplist)

    @patch('transform.transformers.ImageTransformer._get_image_sequence_list', return_value=[13, 14])
    def test_original_json_stored_in_zip(self, mock_sequence_no):  # pylint: disable=unused-argument
        """Compare the dictionary loaded from the zip file json is the same as that submitted"""
        expected_json_data = json.loads(self.test_message)

        zip_contents = self.get_zip_file_contents(self.transform_cs_endpoint + "/2345")

        z = zipfile.ZipFile(zip_contents)
        zfile = z.open('EDC_QJson/023_2345.json', 'r')
        actual_json_data = json.loads(zfile.read().decode('utf-8'))

        self.assertEqual(actual_json_data, expected_json_data)

    def test_invalid_data(self):
        r = self.app.post(self.transform_cs_endpoint, data="rubbish")
        self.assertEqual(r.status_code, 400)
