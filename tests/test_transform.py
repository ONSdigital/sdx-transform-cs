from server import app

import unittest
import glob
import os


def get_file_as_string(filename):

    f = open(filename)
    contents = f.read()

    f.close()

    return contents


def get_test_scenarios(output_type):
    return glob.glob('./tests/%s/*.json' % output_type)


def get_expected_output(filename, output_type):
    filename, ext = os.path.splitext(filename)
    output_filename = "%s.%s" % (filename, output_type)

    print("Loading expected output %s " % output_filename)

    return get_file_as_string(output_filename)


class TestTransformService(unittest.TestCase):

    transform_idbr_endpoint = "/idbr"
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

            r = self.app.post(self.transform_pck_endpoint, data=payload)

            actual_response = r.data.decode('UTF8')

            self.assertEqual(actual_response, expected_response)

    def test_invalid_input(self):
        r = self.app.post(self.transform_pck_endpoint, data="rubbish")

        self.assertEqual(r.status_code, 400)

        r = self.app.post(self.transform_idbr_endpoint, data="rubbish")

        self.assertEqual(r.status_code, 400)

        r = self.app.post(self.transform_images_endpoint, data="rubbish")

        self.assertEqual(r.status_code, 400)

        r = self.app.post(self.transform_pdf_endpoint, data="rubbish")

        self.assertEqual(r.status_code, 400)
