import csv
import glob
import io
import json
import os
import unittest

from transform import app
from transform.views.image_filters import format_date


def get_file_as_string(filename):

    f = open(filename)
    contents = f.read()

    f.close()

    return contents


def get_test_scenarios(output_type):
    return glob.glob('./tests/%s/*.json' % output_type)


def get_expected_file(filename, output_type):
    filename, ext = os.path.splitext(filename)
    return "%s.%s" % (filename, output_type)


def get_expected_output(filename, output_type):
    output_filename = get_expected_file(filename, output_type)

    print("Loading expected output %s " % output_filename)

    return get_file_as_string(output_filename)


def modify_csv_time(csv_content, creation_time):
    expected_csv_file = csv.reader(io.StringIO(csv_content))

    modified_rows = []

    for row in expected_csv_file:
        row[0] = format_date(creation_time)
        row[2] = format_date(creation_time, 'short')

        modified_rows.append(row)

    # Write modified csv to string buffer
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(modified_rows)

    buffer.seek(0)

    # Strip the final newline that csv writer creates
    return buffer.read().rstrip('\r\n')


class TestTransformService(unittest.TestCase):

    transform_idbr_endpoint = "/idbr"
    transform_images_endpoint = "/images"
    # Provide a default batch no as url param
    transform_pck_endpoint = "/pck/30001"
    transform_images_endpoint = "/images"
    transform_pdf_endpoint = "/pdf"

    def setUp(self):

        # creates a test client
        self.app = app.test_client()

        # propagate the exceptions to the test client
        self.app.testing = True

    def test_transforms_idbr(self):

        test_scenarios = get_test_scenarios('idbr')

        print("Found %d idbr scenarios" % len(test_scenarios))

        for scenario_filename in test_scenarios:

            print("Loading scenario %s " % scenario_filename)
            payload = get_file_as_string(scenario_filename)
            expected_response = get_expected_output(scenario_filename, 'idbr')

            r = self.app.post(self.transform_idbr_endpoint, data=payload)

            actual_response = r.data.decode('UTF8')

            self.assertEqual(actual_response, expected_response)

    def test_transforms_pck(self):

        test_scenarios = get_test_scenarios('pck')

        print("Found %d pck scenarios" % len(test_scenarios))

        for scenario_filename in test_scenarios:

            print("Loading scenario %s " % scenario_filename)
            payload = get_file_as_string(scenario_filename)
            expected_response = get_expected_output(scenario_filename, 'pck')
            print("Expected response")
            print(expected_response)

            r = self.app.post(self.transform_pck_endpoint, data=payload)

            actual_response = r.data.decode('UTF8')
            print("Actual response")
            print(actual_response)

            self.assertEqual(actual_response, expected_response)

    def test_invalid_input(self):
        r = self.app.post(self.transform_pck_endpoint, data="rubbish")

        self.assertEqual(r.status_code, 400)

        r = self.app.post(self.transform_idbr_endpoint, data="rubbish")

        self.assertEqual(r.status_code, 400)

    def test_invalid_survey_id(self):
        # Create an invlid survey id payload
        payload_str = get_file_as_string('./tests/pck/023.0203.json')
        payload_object = json.loads(payload_str)
        payload_object['survey_id'] = '666'
        payload = json.dumps(payload_object)

        r = self.app.post(self.transform_pck_endpoint, data=payload)

        self.assertEqual(r.status_code, 400)
