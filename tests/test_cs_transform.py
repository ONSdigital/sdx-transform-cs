import io
import json
import unittest
import zipfile

from transform import app


class TestCSTransformService(unittest.TestCase):

    transform_cs_endpoint = "/common-software"
    test_message = '''{
        "type": "uk.gov.ons.edc.eq:surveyresponse",
        "origin": "uk.gov.ons.edc.eq",
        "survey_id": "023",
        "version": "0.0.1",
        "tx_id": "897fbe8c-fa67-4406-b05c-3e893bc1af78",
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

    vacancies_message = '''{
        "collection": {
            "exercise_sid": "c118471e-f243-484b-ba16-9f78a244c465",
            "instrument_id": "0006",
            "period": "2001"
        },
        "data": {
            "10": "30",
            "146": "This is a comment"
        },
        "flushed": false,
        "metadata": {
            "ref_period_end_date": "2019-01-30",
            "ref_period_start_date": "2020-01-01",
            "ru_ref": "49800108249D",
            "user_id": "UNKNOWN"
        },
        "origin": "uk.gov.ons.edc.eq",
        "started_at": "2020-01-05T10:54:11.548611+00:00",
        "submitted_at": "2020-01-05T14:49:33.448608+00:00",
        "type": "uk.gov.ons.edc.eq:surveyresponse",
        "version": "0.0.1",
        "survey_id": "182",
        "tx_id": "897fbe8c-fa67-4406-b05c-3e893bc1af78",
        "case_id": "4d32d367-d725-49ba-8776-a14f5ae035ee"
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

    def test_creates_cs_defaults(self):

        ziplist = self.get_zip_list(self.transform_cs_endpoint)

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/023_897fbe8cfa674406',
            'EDC_QReceipts/REC1203_897fbe8cfa674406.DAT',
            'EDC_QImages/Images/S897fbe8cfa674406_1.JPG',
            'EDC_QImages/Images/S897fbe8cfa674406_2.JPG',
            'EDC_QImages/Index/EDC_023_20160312_897fbe8cfa674406.csv',
            'EDC_QJson/023_897fbe8cfa674406.json'
        ]

        self.assertEqual(expected, ziplist)

    def test_creates_vacancies_defaults(self):

        zip_contents = self.get_zip_file_contents(self.transform_cs_endpoint, msg_data=self.vacancies_message)
        z = zipfile.ZipFile(zip_contents)
        z.close()
        ziplist = z.namelist()

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/181_897fbe8cfa674406',
            'EDC_QReceipts/REC0501_897fbe8cfa674406.DAT',
            'EDC_QImages/Images/S897fbe8cfa674406_1.JPG',
            'EDC_QImages/Index/EDC_182_20200105_897fbe8cfa674406.csv',
            'EDC_QJson/182_897fbe8cfa674406.json'
        ]

        self.assertEqual(expected, ziplist)

    def test_creates_cs_sequence(self):

        ziplist = self.get_zip_list(self.transform_cs_endpoint + "/2345")

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/023_897fbe8cfa674406',
            'EDC_QReceipts/REC1203_897fbe8cfa674406.DAT',
            'EDC_QImages/Images/S897fbe8cfa674406_1.JPG',
            'EDC_QImages/Images/S897fbe8cfa674406_2.JPG',
            'EDC_QImages/Index/EDC_023_20160312_897fbe8cfa674406.csv',
            'EDC_QJson/023_897fbe8cfa674406.json'
        ]

        self.assertEqual(expected, ziplist)

        ziplist = self.get_zip_list(self.transform_cs_endpoint + "/999")

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/023_897fbe8cfa674406',
            'EDC_QReceipts/REC1203_897fbe8cfa674406.DAT',
            'EDC_QImages/Images/S897fbe8cfa674406_1.JPG',
            'EDC_QImages/Images/S897fbe8cfa674406_2.JPG',
            'EDC_QImages/Index/EDC_023_20160312_897fbe8cfa674406.csv',
            'EDC_QJson/023_897fbe8cfa674406.json'
        ]

        self.assertEqual(expected, ziplist)

    def test_original_json_stored_in_zip(self):
        """Compare the dictionary loaded from the zip file json is the same as that submitted"""
        expected_json_data = json.loads(self.test_message)

        zip_contents = self.get_zip_file_contents(self.transform_cs_endpoint + "/2345")

        z = zipfile.ZipFile(zip_contents)
        zfile = z.open('EDC_QJson/023_897fbe8cfa674406.json', 'r')
        actual_json_data = json.loads(zfile.read().decode('utf-8'))

        self.assertEqual(actual_json_data, expected_json_data)

    def test_invalid_data(self):
        r = self.app.post(self.transform_cs_endpoint, data="rubbish")
        self.assertEqual(r.status_code, 400)
