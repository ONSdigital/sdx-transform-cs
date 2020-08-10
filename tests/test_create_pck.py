import glob
import json
import os
import unittest

from transform.transformers.transform_selector import get_transformer


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

    def transform_pck(self, test_scenarios, output_extension):

        for scenario_filename in test_scenarios:
            print("Loading scenario %s " % scenario_filename)
            payload = get_file_as_dict(scenario_filename)
            expected_response = get_expected_output(scenario_filename, output_extension)
            print("Expected response")
            print(expected_response)

            transformer = get_transformer(payload)
            pck_name, pck = transformer.create_pck()

            actual_response = pck
            print("Actual response")
            print(actual_response)

            self.assertEqual(actual_response, expected_response)

    def test_cs_transforms_pck(self):
        test_scenarios = get_common_software_test_scenarios("pck")
        print("Found %d cs pck scenarios" % len(test_scenarios))
        self.transform_pck(test_scenarios, "nobatch")

    def test_cora_transforms_pck(self):
        """Tests the pck transformation for responses that go to the CORA system."""

        test_scenarios = get_cora_test_scenarios("pck")
        print("Found %d cora pck scenarios" % len(test_scenarios))
        self.transform_pck(test_scenarios, "pck")

    def test_cord_transforms_pck(self):
        """Tests the pck transformation for responses that go to the CORD system."""

        test_scenarios = get_cord_test_scenarios("pck")
        print("Found %d cord pck scenarios" % len(test_scenarios))
        self.transform_pck(test_scenarios, "pck")
