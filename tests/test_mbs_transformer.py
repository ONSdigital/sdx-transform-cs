import unittest

from transform.transformers import MBSTransformer
from transform.transformers.cs_formatter import CSFormatter


class LogicTests(unittest.TestCase):

    response = {
        "origin": "uk.gov.ons.edc.eq",
        "survey_id": "009",
        "tx_id": "40e659ec-013f-4993-9a31-ec1e0ad37888",
        "data": {
            "11": "13/02/2017",
            "12": "14/03/2018",
            "146": "Yes",
            "146a": "Change in level of business activity",
            "146b": "In-store / online promotions",
            "146c": "Special events (e.g. sporting events)",
            "146d": "Calendar events (e.g. Christmas, Easter, Bank Holiday)",
            "146e": "Weather",
            "146f": "Store closures",
            "146g": "Store openings",
            "146h": "Other",
            "40": "100499.49",
            "49": "150500",
            "90": "2900",
            "50": "12",
            "51": "1",
            "52": "2",
            "53": "3",
            "54": "4",
        },
        "type": "uk.gov.ons.edc.eq:surveyresponse",
        "version": "0.0.1",
        "metadata": {"user_id": "K5O86M2NU1", "ru_ref": "12346789012A"},
        "submitted_at": "2017-03-01T14:25:46.101447+00:00",
        "collection": {
            "period": "201605", "exercise_sid": "82R1VDWN74", "instrument_id": "0255"
        },
    }

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
    transformed_no_default_data = MBSTransformer(default_response).transform()

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

    def test_q51(self):
        """
        QId 51 returns an integer.
        """
        self.assertEqual(self.transformed_data["51"], 1)

    def test_q51_not_supplied_is_None(self):
        """
        QId 51 defaults to None if 'd50' is not 'Yes'.
        """
        with self.assertRaises(KeyError):
            self.transformed_no_default_data["51"]

    def test_q51_default(self):
        """
        QId 51 defaults to 0 if 'd50' is 'Yes'.
        """
        self.assertEqual(self.transformed_default_data["51"], 0)

    def test_q52(self):
        """
        QId 52 returns an integer.
        """
        self.assertEqual(self.transformed_data["52"], 2)

    def test_q52_not_supplied_is_None(self):
        """
        QId 52 defaults to None if 'd50' is not 'Yes'.
        """
        with self.assertRaises(KeyError):
            self.transformed_no_default_data["52"]

    def test_q52_default(self):
        """
        QId 52 defaults to 0 if 'd50' is 'Yes'.
        """
        self.assertEqual(self.transformed_default_data["52"], 0)

    def test_q53(self):
        """
        QId 53 returns an integer.
        """
        self.assertEqual(self.transformed_data["53"], 3)

    def test_q53_not_supplied_is_None(self):
        """
        QId 53 defaults to None if 'd50' is not 'Yes'.
        """
        with self.assertRaises(KeyError):
            self.transformed_no_default_data["53"]

    def test_q53_default(self):
        """
        QId 53 defaults to 0 if 'd50' is 'Yes'.
        """
        self.assertEqual(self.transformed_default_data["53"], 0)

    def test_q54(self):
        """
        QId 54 returns an integer.
        """
        self.assertEqual(self.transformed_data["54"], 4)

    def test_q54_not_supplied_is_None(self):
        """
        QId 54 defaults to None if 'd50' is not 'Yes'.
        """
        with self.assertRaises(KeyError):
            self.transformed_no_default_data["54"]

    def test_q54_default(self):
        """
        QId 54 defaults to 0 if 'd50' is 'Yes'.
        """
        self.assertEqual(self.transformed_default_data["54"], 0)


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
