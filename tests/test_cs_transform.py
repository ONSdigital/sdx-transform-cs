from transform import app
from transform.views.test_views import test_message
import unittest
import io
import zipfile
from unittest.mock import patch


class TestCSTransformService(unittest.TestCase):

    transform_cs_endpoint = "/common-software"

    def setUp(self):

        # creates a test client
        self.app = app.test_client()

        # propagate the exceptions to the test client
        self.app.testing = True

    def get_zip_list(self, endpoint):

        r = self.app.post(endpoint, data=test_message)

        zip_contents = io.BytesIO(r.data)

        z = zipfile.ZipFile(zip_contents)
        z.close()

        return z.namelist()

    @patch('transform.transformers.ImageTransformer.get_image_sequence_numbers', return_value=[13])
    def test_creates_cs_defaults(self, mock_sequence_no):

        ziplist = self.get_zip_list(self.transform_cs_endpoint)

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/023_1000',
            'EDC_QReceipts/REC1203_1000.DAT',
            'EDC_QImages/Images/S000000013.JPG',
            'EDC_QImages/Index/EDC_023_20160312_1000.csv'
        ]

        self.assertEqual(expected, ziplist)

    @patch('transform.transformers.ImageTransformer.get_image_sequence_numbers', return_value=[1985])
    def test_creates_cs_sequence(self, mock_sequence_no):

        ziplist = self.get_zip_list(self.transform_cs_endpoint + "/2345")

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/023_2345',
            'EDC_QReceipts/REC1203_2345.DAT',
            'EDC_QImages/Images/S000001985.JPG',
            'EDC_QImages/Index/EDC_023_20160312_2345.csv'
        ]

        self.assertEqual(expected, ziplist)

        ziplist = self.get_zip_list(self.transform_cs_endpoint + "/999")

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/023_0999',
            'EDC_QReceipts/REC1203_0999.DAT',
            'EDC_QImages/Images/S000001985.JPG',
            'EDC_QImages/Index/EDC_023_20160312_0999.csv'
        ]

        self.assertEqual(expected, ziplist)

    def test_invalid_data(self):
        r = self.app.post(self.transform_cs_endpoint, data="rubbish")

        self.assertEqual(r.status_code, 400)
