import glob
import json
import os
import unittest

from transform import app


def get_file_as_string(filename):

    f = open(filename)
    contents = f.read()

    f.close()

    return contents


def get_file_as_dict(filename):

    with open(filename, encoding="utf-8") as fh:
        content = fh.read()
        return json.loads(content)


def get_test_scenarios(output_type):
    return glob.glob("./tests/%s/*.json" % output_type)


def get_common_software_test_scenarios(output_type):
    return glob.glob("./tests/%s/common_software/*.json" % output_type)


def get_cora_test_scenarios(output_type):
    return glob.glob("./tests/%s/cora/*.json" % output_type)


def get_cord_test_scenarios(output_type):
    return glob.glob("./tests/%s/cord/*.json" % output_type)


def get_expected_file(filename, output_type):
    filename, _ = os.path.splitext(filename)
    return "%s.%s" % (filename, output_type)


def get_expected_output(filename, output_type):
    output_filename = get_expected_file(filename, output_type)

    print("Loading expected output %s " % output_filename)

    return get_file_as_string(output_filename)


class TestTransformService(unittest.TestCase):

    transform_images_endpoint = "/images"
    transform_endpoint = "/transform/30001"

    def setUp(self):

        # creates a test client
        self.app = app.test_client()

        # propagate the exceptions to the test client
        self.app.testing = True

    def test_invalid_input(self):
        r = self.app.post(self.transform_endpoint, data="rubbish")

        self.assertEqual(r.status_code, 400)

    def test_invalid_survey_id(self):
        # Create an invalid survey id payload
        payload_str = get_file_as_string("./tests/pck/common_software/023.0203.json")
        payload_object = json.loads(payload_str)
        payload_object["survey_id"] = "666"
        payload = json.dumps(payload_object)

        r = self.app.post(self.transform_endpoint, data=payload)

        self.assertEqual(r.status_code, 400)
