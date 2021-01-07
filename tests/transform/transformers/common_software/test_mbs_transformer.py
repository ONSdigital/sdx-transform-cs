import datetime
import itertools
import json
import unittest
from copy import deepcopy

from transform.transformers.common_software import MBSTransformer
from transform.transformers.common_software.cs_formatter import CSFormatter
from transform.transformers.transform_selector import get_transformer


class LogicTests(unittest.TestCase):
    with open("tests/replies/009.0255.json", "r") as fp:
        response = json.load(fp)

    transformed_data = MBSTransformer(response)._transform()

    # To test default values this creates a transformed dict with no keys for 51:54
    # and a key:val pair of 'd50': 'Yes'
    default_response = response.copy()
    for k in ["51", "52", "53", "54"]:
        del default_response["data"][k]

    default_response["data"]["d50"] = "Yes"
    transformed_default_data = MBSTransformer(default_response)._transform()

    # When no values are supplied for q_codes 51:54 no entries should be present
    # in the PCK file
    del default_response["data"]["d50"]

    # If d12 is "Yes", then nothing for dates go to the PCK.
    del default_response["data"]["11"]
    del default_response["data"]["12"]
    default_response["d12"] = "Yes"

    transformed_no_default_data = MBSTransformer(default_response)._transform()

    def test_potable_water(self):
        """
        QId 110 returns a whole number as n integer.
        """
        self.assertEqual(self.transformed_data["110"], 256)

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

    def test_comments(self):
        """
        QId 146 returns 1 if comments present, 2 otherwise.
        """
        self.assertEqual(self.transformed_data["146"], 1)

        no_turnover_response = dict.copy(self.response)
        print(no_turnover_response)
        del no_turnover_response["data"]["146"]
        print(no_turnover_response)
        no_turnover_transformed = MBSTransformer(no_turnover_response)._transform()

        self.assertEqual(no_turnover_transformed["146"], 2)

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
        rounded_up_transformed = MBSTransformer(rounded_up_response)._transform()
        self.assertEqual(rounded_up_transformed["40"], 101)

    def test_turnover_excluding_vat_rounds_half_up_when_equal(self):
        """
        QId 40 returns a Decimal rounded up to nearest 1000 then divided by 1000.
        """
        rounded_up_response = dict.copy(self.response)
        rounded_up_response["data"]["40"] = "1234500.00"
        rounded_up_transformed = MBSTransformer(rounded_up_response)._transform()
        self.assertEqual(rounded_up_transformed["40"], 1235)

    def test_turnover_excluding_vat_rounds_half_up(self):
        """
        QId 40 returns a Decimal rounded half up to nearest 1000 then divided by 1000.
        """
        rounded_up_response = dict.copy(self.response)
        rounded_up_response["data"]["40"] = "10499.50"
        rounded_up_transformed = MBSTransformer(rounded_up_response)._transform()
        self.assertEqual(rounded_up_transformed["40"], 11)

    def test_value_of_exports(self):
        """
        QId 49 returns a Decimal rounded down to nearest 1000 then divided by 1000.
        """
        self.assertEqual(self.transformed_data["49"], 151)

    def test_value_of_excise_duty(self):
        """
        QId 90 returns a Decimal rounded down to nearest 1000 then divided by 1000.
        """
        self.assertEqual(self.transformed_data["90"], 3)

    def test_value_number_of_employees(self):
        """
        QId 50 returns int.
        """
        self.assertEqual(self.transformed_data["50"], 12)

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
        self.assertEqual(
            self.transformed_no_default_data["11"], datetime.date(2018, 1, 1)
        )
        self.assertEqual(
            self.transformed_no_default_data["12"], datetime.date(2018, 3, 1)
        )


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

    def test_load_survey_fails(self):
        """
        Tests if load data fails if an id is unavailable
        """

        response = {
            "survey_id": "009",
            "tx_id": "27923934-62de-475c-bc01-433c09fd38b8",
            "collection": {"instrument_id": "0255", "period": "201704"},
            "metadata": {"user_id": "123456789", "ru_ref": "12345678901A"},
        }

        transformer = MBSTransformer(response)
        del (transformer.response["survey_id"])
        ids = transformer.get_identifiers()
        self.assertIsNone(ids)


class TestTransform(unittest.TestCase):
    response = {
        "origin": "uk.gov.ons.edc.eq",
        "survey_id": "009",
        "tx_id": "40e659ec-013f-4993-9a31-ec1e0ad37888",
        "data": {
            "11": "13/02/2017",
            "12": "14/03/2018",
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
        "metadata": {
            "user_id": "K5O86M2NU1",
            "ru_ref": "12346789012A",
            "ref_period_start_date": "2018-01-01",
            "ref_period_end_date": "2018-03-01",
        },
        "submitted_at": "2017-03-01T14:25:46.101447+00:00",
        "collection": {
            "period": "201605", "exercise_sid": "82R1VDWN74", "instrument_id": "0255"
        },
    }

    response_d50_d49_yes = {
        "origin": "uk.gov.ons.edc.eq",
        "survey_id": "009",
        "tx_id": "40e659ec-013f-4993-9a31-ec1e0ad37888",
        "data": {
            "11": "13/02/2017",
            "12": "14/03/2018",
            "146": "Yes",
            "d49": "Yes",
            "90": "2900",
            "d50": "Yes",
        },
        "type": "uk.gov.ons.edc.eq:surveyresponse",
        "version": "0.0.1",
        "metadata": {
            "user_id": "K5O86M2NU1",
            "ru_ref": "12346789012A",
            "ref_period_start_date": "2018-01-01",
            "ref_period_end_date": "2018-03-01",
        },
        "submitted_at": "2017-03-01T14:25:46.101447+00:00",
        "collection": {
            "period": "201605", "exercise_sid": "82R1VDWN74", "instrument_id": "0255"
        },
    }

    def test_convert_string_to_int(self):
        value = MBSTransformer(self.response).convert_str_to_int(None)
        self.assertIsNone(value)

    def test_convert_string_to_negative_int(self):
        value = MBSTransformer(self.response).convert_str_to_int("-1")
        self.assertEqual(value, -1)

    def test_convert_string_float_to_intraises_value_error(self):
        with self.assertRaises(ValueError):
            MBSTransformer(self.response).convert_str_to_int("1.5")

    def test_check_employee_totals_no_d50(self):
        result = MBSTransformer(self.response).check_employee_totals()
        self.assertEqual(result, {"51": 1, "52": 2, "53": 3, "54": 4})

    def test_check_employee_totals_d50_yes(self):
        result = MBSTransformer(self.response_d50_d49_yes).check_employee_totals()
        self.assertEqual(result, {"51": 0, "52": 0, "53": 0, "54": 0})

    def test_check_employee_totals_missing_q_codes(self):
        local_response = deepcopy(self.response)
        del (local_response["data"]["51"])
        result = MBSTransformer(local_response).check_employee_totals()
        self.assertEqual(result, {"51": None, "52": 2, "53": 3, "54": 4})

    def test_check_turnover_totals_no_d49(self):
        result = MBSTransformer(self.response).check_turnover_totals()
        self.assertEqual(result, {"49": 151})

    def test_check_turnover_totals_d49_yes(self):
        result = MBSTransformer(self.response_d50_d49_yes).check_turnover_totals()
        self.assertEqual(result, {"49": 0})

    def test_check_turnover_totals_missing_q_codes(self):
        local_response = deepcopy(self.response)
        del (local_response["data"]["49"])
        result = MBSTransformer(local_response).check_turnover_totals()
        self.assertEqual(result, {"49": None})

    def test_survey_date_no_dates_submitted(self):
        local_response = deepcopy(self.response)
        del (local_response["data"]["11"])
        del (local_response["data"]["12"])
        result = MBSTransformer(local_response).survey_dates()
        self.assertEqual(
            result,
            {
                "11": datetime.date(2018, 1, 1),
                "12": datetime.date(2018, 3, 1),
            },
        )

    def test_survey_date_dates_submitted(self):
        response = deepcopy(self.response)
        result = MBSTransformer(response).survey_dates()
        self.assertEqual(
            result,
            {
                "11": datetime.date(2017, 2, 13),
                "12": datetime.date(2018, 3, 14),
            },
        )

    def test_survey_date_raises_attribute_error(self):
        local_response = deepcopy(self.response)
        del (local_response["data"]["11"])
        del (local_response["data"]["12"])
        del (local_response["metadata"]["ref_period_start_date"])

        with self.assertRaises(KeyError):
            MBSTransformer(local_response).survey_dates()

        local_response = deepcopy(self.response)
        del (local_response["data"]["11"])
        del (local_response["data"]["12"])
        del (local_response["metadata"]["ref_period_end_date"])

        with self.assertRaises(KeyError):
            MBSTransformer(local_response).survey_dates()

        local_response = deepcopy(self.response)
        del (local_response["data"]["11"])
        del (local_response["data"]["12"])
        del (local_response["metadata"]["ref_period_end_date"])
        del (local_response["metadata"]["ref_period_start_date"])

        with self.assertRaises(KeyError):
            MBSTransformer(local_response).survey_dates()

    def test_period_date_29_06_2018(self):
        response = deepcopy(self.response)
        result = MBSTransformer(response)
        result.response['data'].update({
            '11': '29/06/2018',
            '12': '31/07/2018'
        })
        result = result.survey_dates()
        expected = {
            "11": datetime.date(2018, 6, 29),
            "12": datetime.date(2018, 7, 31)
        }

        self.assertEqual(result, expected)

    def test_period_date_less_than_6_characters(self):
        response = deepcopy(self.response)
        result = MBSTransformer(response)
        result.response['data'].update({
            '11': '3',
            '12': '5'
        })
        result = result.survey_dates()

        self.assertEqual(result, {'11': None, '12': None})

    def test_period_date_empty_string(self):
        response = deepcopy(self.response)
        result = MBSTransformer(response)
        result.response['data'].update({
            '11': '',
            '12': ''
        })
        result = result.survey_dates()

        self.assertEqual(result, {'11': None, '12': None})

    def test_period_date_with_6_blank_characters(self):
        response = deepcopy(self.response)
        result = MBSTransformer(response)
        result.response['data'].update({
            '11': '      ',
            '12': '      '
        })
        result = result.survey_dates()

        self.assertEqual(result, {'11': None, '12': None})

    def test_period_date_with_blank_characters_before_and_after_date(self):
        response = deepcopy(self.response)
        result = MBSTransformer(response)
        result.response['data'].update({
            '11': '    2018/02/23    ',
            '12': '    2018/04/01    '
        })
        result = result.survey_dates()

        self.assertEqual(result, {'11': None, '12': None})

    def test_period_date_ends_with_Z(self):
        response = deepcopy(self.response)
        result = MBSTransformer(response)
        result.response['data'].update({
            '11': '2018-06-29T10:20:30Z',
            '12': '2018-07-30T10:20:30Z'
        })

        expected = {
            '11': datetime.datetime(2018, 6, 29, 10, 20, 30, tzinfo=datetime.timezone.utc),
            '12': datetime.datetime(2018, 7, 30, 10, 20, 30, tzinfo=datetime.timezone.utc)
        }

        result = result.survey_dates()
        self.assertEqual(result, expected)

    def test_mbs_create_zip(self):
        response = deepcopy(self.response)
        transformer = get_transformer(response, 0)

        transformer.get_zip(img_seq=itertools.count())

        actual = transformer.image_transformer.zip.get_filenames()

        expected = [
            'EDC_QData/009_40e659ec013f4993',
            'EDC_QReceipts/REC0103_40e659ec013f4993.DAT',
            'EDC_QImages/Images/S40e659ec013f4993_1.JPG',
            'EDC_QImages/Images/S40e659ec013f4993_2.JPG',
            'EDC_QImages/Index/EDC_009_20170301_40e659ec013f4993.csv',
            'EDC_QJson/009_40e659ec013f4993.json'
        ]
        self.assertEqual(expected, actual)

    def test_comment_results_in_1(self):
        response = deepcopy(self.response)
        response['data']["146"] = "This is a comment"
        result = MBSTransformer(response)._transform()
        self.assertEqual(1, result["146"])

    def test_empty_comment_results_in_1(self):
        response = deepcopy(self.response)
        response['data']["146"] = " "
        result = MBSTransformer(response)._transform()
        self.assertEqual(1, result["146"])

    def test_no_comment_results_in_2(self):
        response = deepcopy(self.response)
        result = MBSTransformer(response)._transform()
        self.assertEqual(2, result["146"])
