import json
import unittest

from transform.transformers import MBSTransformer
from transform.transformers.cs_formatter import CSFormatter


class LogicTests(unittest.TestCase):

    with open("tests/replies/009.0255.json", "r") as fp:
        response = json.load(fp)

    transformed_data = MBSTransformer(response).transform()

    # To test default values this creates a transformed dict with no keys for 51:54
    # and a key:val pair of 'd50': 'Yes'
    default_response = response.copy()
    for k in ["51", "52", "53", "54"]:
        del default_response["data"][k]

    default_response["data"]["d50"] = "Yes"
    transformed_default_data = MBSTransformer(default_response).transform()

    # When no values are supplied for q_codes 51:54 no entries should be present
    # in the PCK file
    del default_response["data"]["d50"]

    # If d12 is "Yes", then nothing for dates go to the PCK.
    del default_response["data"]["11"]
    del default_response["data"]["12"]
    default_response["d12"] = "Yes"

    transformed_no_default_data = MBSTransformer(default_response).transform()

    def test_potable_water(self):
        """
        QId 110 returns a whole number as a string.
        """
        self.assertEqual(self.transformed_data["110"], "256")

    def test_reporting_period_from(self):
        """
        QId 11 specifies the date the reporting period starts.
        """
        self.assertEqual(13, self.transformed_data["11"].day)
        self.assertEqual(2, self.transformed_data["11"].month)
        self.assertEqual(2017, self.transformed_data["11"].year)

    def test_reporting_period_to(self):
        """
        QId 12 specifies the date the reporting period ends.
        """
        self.assertEqual(14, self.transformed_data["12"].day)
        self.assertEqual(3, self.transformed_data["12"].month)
        self.assertEqual(2018, self.transformed_data["12"].year)

    def test_turnover_radio(self):
        """
        QId 146 returns Yes.
        """
        self.assertEqual(self.transformed_data["146"], 1)

        no_turnover_response = dict.copy(self.response)
        no_turnover_response["data"]["146"] = "No"
        no_turnover_transformed = MBSTransformer(no_turnover_response).transform()

        self.assertEqual(no_turnover_transformed["146"], False)

    def test_turnover_excluding_vat_rounds_down(self):
        """
        QId 40 returns a Decimal rounded down to nearest 1000 then divided by 1000.
        """
        self.assertEqual(self.transformed_data["40"], 100)

    def test_turnover_excluding_vat_rounds_up(self):
        """
        QId 40 returns a Decimal rounded up to nearest 1000 then divided by 1000.
        """
        rounded_up_response = dict.copy(self.response)
        rounded_up_response["data"]["40"] = "100501.00"
        rounded_up_transformed = MBSTransformer(rounded_up_response).transform()
        self.assertEqual(rounded_up_transformed["40"], 101)

    def test_turnover_excluding_vat_rounds_half_up(self):
        """
        QId 40 returns a Decimal rounded half up to nearest 1000 then divided by 1000.
        """
        rounded_up_response = dict.copy(self.response)
        rounded_up_response["data"]["40"] = "10499.50"
        rounded_up_transformed = MBSTransformer(rounded_up_response).transform()
        self.assertEqual(rounded_up_transformed["40"], 11)

    def test_value_of_exports(self):
        """
        QId 49 returns a Decimal rounded down to nearest 1000 then divided by 1000.
        """
        self.assertEqual(self.transformed_data["49"], 151)

    def test_value_of_excise_duty(self):
        """
        QId 49 returns a Decimal rounded down to nearest 1000 then divided by 1000.
        """
        self.assertEqual(self.transformed_data["90"], 3)

    def test_value_number_of_employees(self):
        """
        QId 50 returns string.
        """
        self.assertEqual(self.transformed_data["50"], "12")

    def test_male_employees_working_more_than_30(self):
        """
        QId 51 returns an integer.
        """
        self.assertEqual(self.transformed_data["51"], 1)

    def test_male_employees_working_more_than_30_not_supplied_is_None(self):
        """
        QId 51 defaults to None if 'd50' is not 'Yes'.
        """
        with self.assertRaises(KeyError):
            self.transformed_no_default_data["51"]

    def test_male_employees_working_more_than_30_default(self):
        """
        QId 51 defaults to 0 if 'd50' is 'Yes'.
        """
        self.assertEqual(self.transformed_default_data["51"], 0)

    def test_male_employees_working_less_than_30(self):
        """
        QId 52 returns an integer.
        """
        self.assertEqual(self.transformed_data["52"], 2)

    def test_male_employees_working_less_than_30_not_supplied_is_None(self):
        """
        QId 52 defaults to None if 'd50' is not 'Yes'.
        """
        with self.assertRaises(KeyError):
            self.transformed_no_default_data["52"]

    def test_male_employees_working_less_than_30_default(self):
        """
        QId 52 defaults to 0 if 'd50' is 'Yes'.
        """
        self.assertEqual(self.transformed_default_data["52"], 0)

    def test_female_employees_working_more_than_30(self):
        """
        QId 53 returns an integer.
        """
        self.assertEqual(self.transformed_data["53"], 3)

    def test_female_employees_working_more_than_30_not_supplied_is_None(self):
        """
        QId 53 defaults to None if 'd50' is not 'Yes'.
        """
        with self.assertRaises(KeyError):
            self.transformed_no_default_data["53"]

    def test_female_employees_working_more_than_30_default(self):
        """
        QId 53 defaults to 0 if 'd50' is 'Yes'.
        """
        self.assertEqual(self.transformed_default_data["53"], 0)

    def test_female_employees_working_less_than_30(self):
        """
        QId 54 returns an integer.
        """
        self.assertEqual(self.transformed_data["54"], 4)

    def test_female_employees_working_more_less_30_not_supplied_is_None(self):
        """
        QId 54 defaults to None if 'd50' is not 'Yes'.
        """
        with self.assertRaises(KeyError):
            self.transformed_no_default_data["54"]

    def test_female_employees_working_more_less_30_default(self):
        """
        QId 54 defaults to 0 if 'd50' is 'Yes'.
        """
        self.assertEqual(self.transformed_default_data["54"], 0)

    def test_no_dates_submitted(self):
        """
        Qid d12 is Yes and no Qid 11 or 12
        """
        self.transformed_no_default_data["11"] is None
        self.transformed_no_default_data["12"] is None


class BatchFileTests(unittest.TestCase):

    def test_pck_form_header(self):
        """
        Test package form header
        """
        form_id = "MB65B"
        ru_ref = 49900108249
        check = "D"
        period = "1704"
        return_value = CSFormatter._pck_form_header(form_id, ru_ref, check, period)
        self.assertEqual("MB65B:49900108249D:1704", return_value)

    def test_load_survey(self):
        """
        Tests if load data passes if survey id is 009
        """

        response = {
            "survey_id": "009",
            "tx_id": "27923934-62de-475c-bc01-433c09fd38b8",
            "collection": {"instrument_id": "0255", "period": "201704"},
            "metadata": {"user_id": "123456789", "ru_ref": "12345678901A"},
        }

        transformer = MBSTransformer(response)
        ids = transformer.get_identifiers()
        self.assertIsInstance(ids, dict)
        self.assertIsNotNone(ids)
