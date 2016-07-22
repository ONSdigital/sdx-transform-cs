from transform import app
from tests.test_transform import get_file_as_string, get_test_scenarios, get_expected_output
import unittest


class TestNoBatchTransformService(unittest.TestCase):

    transform_pck_endpoint = "/pck"

    def setUp(self):

        # creates a test client
        self.app = app.test_client()

        # propagate the exceptions to the test client
        self.app.testing = True

    def test_transforms_no_batch(self):

        test_scenarios = get_test_scenarios('pck')
        print("Found %d nobatch/pck scenarios" % len(test_scenarios))

        for scenario_filename in test_scenarios:
            print("Loading scenario %s " % scenario_filename)
            payload = get_file_as_string(scenario_filename)
            expected_response = get_expected_output(scenario_filename, 'nobatch')

            r = self.app.post(self.transform_pck_endpoint, data=payload)

            actual_response = r.data.decode('UTF8')

            self.assertEqual(actual_response, expected_response)
