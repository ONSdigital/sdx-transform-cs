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


def get_expected_file(filename, output_type):
    filename, _ = os.path.splitext(filename)
    return "%s.%s" % (filename, output_type)


def get_expected_output(filename, output_type):
    output_filename = get_expected_file(filename, output_type)

    print("Loading expected output %s " % output_filename)

    return get_file_as_string(output_filename)


class TestTransformService(unittest.TestCase):

    def test_transforms_idbr(self):

        test_scenarios = get_test_scenarios("idbr")

        print("Found %d idbr scenarios" % len(test_scenarios))

        for scenario_filename in test_scenarios:

            print("Loading scenario %s " % scenario_filename)
            payload = get_file_as_dict(scenario_filename)
            expected_response = get_expected_output(scenario_filename, "idbr")

            transformer = get_transformer(payload)
            receipt_name, receipt = transformer.create_receipt()

            actual_response = receipt

            self.assertEqual(actual_response, expected_response)
