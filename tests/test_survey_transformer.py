import csv
from datetime import datetime
import glob
import io
import json
import os
import unittest
import zipfile
import dateutil

from transform.transformers.transform_selector import get_transformer
from transform.utilities.formatter import Formatter
from transform.views.image_filters import format_date


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


def modify_csv_time(csv_content, creation_time):
    expected_csv_file = csv.reader(io.StringIO(csv_content))

    modified_rows = []

    for row in expected_csv_file:
        row[0] = format_date(creation_time)
        row[2] = format_date(creation_time, "short")

        modified_rows.append(row)

    # Write modified csv to string buffer
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(modified_rows)

    buffer.seek(0)

    # Strip the final newline that csv writer creates
    return buffer.read().rstrip("\r\n")


class TestSurveyTransformer(unittest.TestCase):

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

    def test_create_cs_pck(self):
        test_scenarios = get_common_software_test_scenarios("pck")
        print("Found %d cs pck scenarios" % len(test_scenarios))
        self.transform_pck(test_scenarios, "nobatch")

    def test_create_cora_pck(self):
        """Tests the pck transformation for responses that go to the CORA system."""

        test_scenarios = get_cora_test_scenarios("pck")
        print("Found %d cora pck scenarios" % len(test_scenarios))
        self.transform_pck(test_scenarios, "pck")

    def test_create_cord_pck(self):
        """Tests the pck transformation for responses that go to the CORD system."""

        test_scenarios = get_cord_test_scenarios("pck")
        print("Found %d cord pck scenarios" % len(test_scenarios))
        self.transform_pck(test_scenarios, "pck")

    def test_create_receipt(self):

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

    def test_create_index(self):
        test_scenarios = get_test_scenarios("csv")

        print("Found %d csv scenarios" % len(test_scenarios))

        for scenario_filename in test_scenarios:
            print("Loading scenario %s " % scenario_filename)

            payload = get_file_as_string(scenario_filename)
            payload_object = json.loads(payload)

            transformer = get_transformer(payload_object, 1000)

            z = zipfile.ZipFile(transformer.image_transformer.get_zipped_images().in_memory_zip)

            expected_content = get_expected_output(scenario_filename, "csv")
            expected_csv = list(csv.reader(io.StringIO(expected_content)))

            date_object = datetime.strptime(expected_csv[0][0], "%d/%m/%Y %H:%M:%S")

            sub_date = dateutil.parser.parse(payload_object["submitted_at"])
            sub_date_str = sub_date.strftime("%Y%m%d")

            filename = "EDC_QImages/Index/EDC_{}_{}_{}.csv".format(payload_object["survey_id"], sub_date_str,
                                                                   Formatter._get_tx_code(payload_object["tx_id"]))
            self.assertIn(filename, z.namelist())

            edc_file = z.open(filename)
            actual_content = edc_file.read().decode("utf-8")

            modified_content = modify_csv_time(actual_content, date_object)
            modified_csv = list(csv.reader(io.StringIO(modified_content)))

            self.assertEqual(expected_csv, modified_csv)
