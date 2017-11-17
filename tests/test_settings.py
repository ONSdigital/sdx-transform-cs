import os
import transform.settings
import unittest


class TestNoBatchTransformService(unittest.TestCase):
    def setUp(self):
        os.environ["SDX_SEQUENCE_URL"] = "SomeUrl"

    def test_get_value_returns_environment_value(self):
        sdx_sequence_url = transform.settings._get_value("SDX_SEQUENCE_URL")
        self.assertEquals(sdx_sequence_url, "SomeUrl")

    def test_get_value_returns_default_if_no_environment_variable_found(self):
        val = transform.settings._get_value("SOME_UNKNOWN_ENV", "SomeDefaultValue")
        self.assertEquals(val, "SomeDefaultValue")

    def test_get_value_raises_ValueError_if_no_enviornment_variable_and_no_default(self):
        with self.assertRaises(ValueError):
            transform.settings._get_value("SOME_UNKNOWN_ENV")

    def test_get_raises_ValueError_if_empty_string_set_as_default(self):
        with self.assertRaises(ValueError):
            transform.settings._get_value("SOME_UNKNOWN_ENV", "")
