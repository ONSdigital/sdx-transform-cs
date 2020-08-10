import csv
import glob
import io
import json
import os
import unittest
import zipfile
from datetime import datetime
from unittest.mock import patch

import dateutil

from transform import app
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


class TestTransformService(unittest.TestCase):

    transform_images_endpoint = "/images"
    transform_endpoint = "/transform/30001"

    def setUp(self):

        # creates a test client
        self.app = app.test_client()

        # propagate the exceptions to the test client
        self.app.testing = True

    @patch("transform.transformers.ImageTransformer._get_image_sequence_list", return_value=[1, 2])
    def test_transforms_csv(self, mock_sequence_no):
        test_scenarios = get_test_scenarios("csv")

        print("Found %d csv scenarios" % len(test_scenarios))

        for scenario_filename in test_scenarios:

            print("Loading scenario %s " % scenario_filename)

            payload = get_file_as_string(scenario_filename)
            payload_object = json.loads(payload)

            r = self.app.post(self.transform_images_endpoint, data=payload)

            zip_contents = io.BytesIO(r.data)

            z = zipfile.ZipFile(zip_contents)

            expected_content = get_expected_output(scenario_filename, "csv")
            expected_csv = list(csv.reader(io.StringIO(expected_content)))

            date_object = datetime.strptime(expected_csv[0][0], "%d/%m/%Y %H:%M:%S")

            sub_date = dateutil.parser.parse(payload_object["submitted_at"])
            sub_date_str = sub_date.strftime("%Y%m%d")

            filename = "EDC_{}_{}_1000.csv".format(payload_object["survey_id"], sub_date_str)
            self.assertIn(filename, z.namelist())

            edc_file = z.open(filename)
            actual_content = edc_file.read().decode("utf-8")

            modified_content = modify_csv_time(actual_content, date_object)
            modified_csv = list(csv.reader(io.StringIO(modified_content)))

            self.assertEqual(expected_csv, modified_csv)

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
