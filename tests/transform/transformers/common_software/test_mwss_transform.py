import datetime
import itertools
import json
import unittest
import zipfile
from collections import OrderedDict

import pytest

from transform.transformers.common_software.cs_formatter import CSFormatter
from transform.transformers.common_software.mwss_transformer import MWSSTransformer
from transform.transformers.processor import Processor
from transform.transformers.survey import Survey, MissingIdsException, MissingSurveyException
from transform.transformers.transform_selector import get_transformer


class SurveyTests(unittest.TestCase):

    def test_datetime_ms_with_colon_in_timezone(self):
        """
        Test datetime with colon

        """
        return_value = Survey.parse_timestamp("2017-01-11T17:18:53.020222+00:00")
        self.assertIsInstance(return_value, datetime.datetime)

    def test_datetime_ms_with_timezone(self):
        """
        Tests datetime with no colon

        """
        return_value = Survey.parse_timestamp("2017-01-11T17:18:53.020222+0000")
        self.assertIsInstance(return_value, datetime.datetime)

    def test_datetime_zulu(self):
        """
        Tests zulu datetime

        """
        return_value = Survey.parse_timestamp("2017-01-11T17:18:53Z")
        self.assertIsInstance(return_value, datetime.datetime)

    def test_date_iso(self):
        """
        Tests iso datetime format

        """
        return_value = Survey.parse_timestamp("2017-01-11")
        self.assertNotIsInstance(return_value, datetime.datetime)
        self.assertIsInstance(return_value, datetime.date)

    def test_date_diary(self):
        """
        Tests date date diary datetime format

        """
        return_value = Survey.parse_timestamp("11/07/2017")
        self.assertNotIsInstance(return_value, datetime.datetime)
        self.assertIsInstance(return_value, datetime.date)


class OpTests(unittest.TestCase):

    def test_processor_unsigned(self):
        """
        Test using unsigned integer for range checking

        """
        proc = Processor.unsigned_integer

        # Supply int default for range checking
        self.assertEqual(0, proc("question_id", {"question_id": -1.24}, 0))
        self.assertEqual(0, proc("question_id", {"question_id": 0.49}, 0))
        self.assertEqual(1, proc("question_id", {"question_id": 1}, 0))
        self.assertEqual(100, proc("question_id", {"question_id": 1E2}, 0))
        self.assertEqual(1000000000, proc("question_id", {"question_id": 1E9}, 0))

        # Supply bool default for range checking and type coercion
        self.assertIs(False, proc("question_id", {"question_id": -1}, False))
        self.assertIs(False, proc("question_id", {"question_id": 0}, False))
        self.assertIs(True, proc("question_id", {"question_id": 1}, False))
        self.assertIs(True, proc("question_id", {"question_id": 1E2}, False))
        self.assertIs(True, proc("question_id", {"question_id": 1E9}, False))
        self.assertIs(False, proc("question_id", {"question_id": 0}, False))

    def test_processor_percentage(self):
        """
        Test using percentage for range checking

        """
        proc = Processor.percentage

        # Supply int default for range checking
        self.assertEqual(0, proc("question_id", {"question_id": -1}, 0))
        self.assertEqual(0, proc("question_id", {"question_id": 0}, 0))
        self.assertEqual(100, proc("question_id", {"question_id": 100}, 0))
        self.assertEqual(0, proc("question_id", {"question_id": 0}, 0))

        # Supply bool default for range checking and type coercion
        self.assertIs(False, proc("question_id", {"question_id": -1}, False))
        self.assertIs(False, proc("question_id", {"question_id": 0}, False))
        self.assertIs(True, proc("question_id", {"question_id": 100}, False))
        self.assertIs(False, proc("question_id", {"question_id": 0}, False))

    def test_ops(self):
        """
        Test response format is valid

        """
        response = {
            "survey_id": "134",
            "tx_id": "27923934-62de-475c-bc01-433c09fd38b8",
            "collection": {
                "instrument_id": "0005",
                "period": "201704"
            },
            "metadata": {
                "user_id": "123456789",
                "ru_ref": "12345678901A"
            },
            "submitted_at": "2017-04-12T13:01:26Z",
        }
        transformer = MWSSTransformer(response, 0)
        self.assertTrue(transformer)


class LogicTests(unittest.TestCase):

    def test_weekly_increase(self):
        """
        Increase in weekly pay (100).

        """
        _, funct = MWSSTransformer.ops()["100"]
        return_value = funct("100", {"100": "6.0"}, 0)
        self.assertEqual(6, return_value)

    def test_aggregate_weekly_paid_employees(self):
        """
        question_id 40, 40f are added to give a value for weekly paid employees (40).

        """
        _, funct = MWSSTransformer.ops()["40"]
        return_value = funct("40", {"40": "125000"}, 0)
        self.assertEqual(125000, return_value)
        return_value = funct("40", {"40": "125000", "40f": "25000"}, 0)
        self.assertEqual(150000, return_value)

    def test_aggregate_fortnightly_gross_pay(self):
        """
        Fortnightly gross pay (50f) is divided by 2 and added to
        the value for question_id 50.

        """
        _, funct = MWSSTransformer.ops()["50"]
        return_value = funct("50", {"50f": "1600"}, 0)
        self.assertEqual(800, return_value)
        return_value = funct("50", {"50": "19200", "50f": "1600"}, 0)
        self.assertEqual(20000, return_value)
        return_value = funct("50", {"50": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("50", {"50": "19200.5", "50f": "1600.5"}, 0)
        self.assertEqual(20001, return_value)
        return_value = funct("50", {"50": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("50", {"50": "19200.02", "50f": "1600.02"}, 0)
        self.assertEqual(20000, return_value)

    def test_aggregate_fortnightly_bonuses(self):
        """
        Fortnightly holiday pay (60f), arrears of pay (70f) and bonuses (80f)
        are divided by 2 and added to question_id 60, 70, 80 respectively.

        """
        _, funct = MWSSTransformer.ops()["60"]
        return_value = funct("60", {"60f": "360"}, 0)
        self.assertEqual(180, return_value)
        return_value = funct("60", {"60": "4600", "60f": "360"}, 0)
        self.assertEqual(4780, return_value)
        return_value = funct("60", {"60": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("60", {"60": "19200.5", "60f": "1600.5"}, 0)
        self.assertEqual(20001, return_value)
        return_value = funct("60", {"60": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("60", {"60": "19200.02", "60f": "1600.02"}, 0)
        self.assertEqual(20000, return_value)

        _, funct = MWSSTransformer.ops()["70"]
        return_value = funct("70", {"70f": "1280"}, 0)
        self.assertEqual(640, return_value)
        return_value = funct("70", {"70": "7360", "70f": "1280"}, 0)
        self.assertEqual(8000, return_value)
        return_value = funct("70", {"70": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("70", {"70": "19200.5", "70f": "1600.5"}, 0)
        self.assertEqual(20001, return_value)
        return_value = funct("70", {"70": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("70", {"70": "19200.02", "70f": "1600.02"}, 0)
        self.assertEqual(20000, return_value)

        _, funct = MWSSTransformer.ops()["80"]
        return_value = funct("80", {"80f": "5000"}, 0)
        self.assertEqual(2500, return_value)
        return_value = funct("80", {"80": "15000", "80f": "5000"}, 0)
        self.assertEqual(17500, return_value)
        return_value = funct("80", {"80": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("80", {"80": "19200.5", "80f": "1600.5"}, 0)
        self.assertEqual(20001, return_value)
        return_value = funct("80", {"80": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("80", {"80": "19200.02", "80f": "1600.02"}, 0)
        self.assertEqual(20000, return_value)

    def test_aggregate_fortnightly_increase(self):
        """
        Increase in Fortnightly pay (100f); aggregated with weekly increase (100).

        """
        _, funct = MWSSTransformer.ops()["100"]
        return_value = funct("100", {"100f": "6.0"}, 0)
        self.assertEqual(6, return_value)
        return_value = funct("100", {"100": "7.0", "100f": "6.0"}, 0)
        self.assertEqual(6, return_value)  # Integer default
        return_value = funct("100", {"100": "7.0", "100f": "6.0"}, 0.0)
        self.assertEqual(6.5, return_value)  # Float default

    def test_aggregate_fortnightly_increase_date(self):
        """
        Date of increase in Fortnightly pay (110f); aggregated with weekly (110).

        """
        _, funct = MWSSTransformer.ops()["110"]
        return_value = funct(
            "110", {"110": "2017-01-09", "110f": "2017-01-11"}, datetime.date.today(),
        )
        self.assertEqual(9, return_value[0].day)
        self.assertEqual(11, return_value[1].day)

    def test_aggregate_fortnightly_increase_employees(self):
        """
        Employees with increase in Fortnightly pay (120f);
        aggregated with weekly increase (120).

        """
        _, funct = MWSSTransformer.ops()["120"]
        return_value = funct("120", {"120f": "60"}, 0)
        self.assertEqual(60, return_value)
        return_value = funct("120", {"120": "40", "120f": "41"}, 0)
        self.assertEqual(40, return_value)  # Integer default
        return_value = funct("120", {"120": "40", "120f": "41"}, 0.0)
        self.assertEqual(40.5, return_value)  # Float default

    def test_aggregate_fortnightly_changes(self):
        """
        question_id 90f used for fortnightly changes question; aggregates to 90.

        """
        _, funct = MWSSTransformer.ops()["90"]
        return_value = funct("90", {"90f": ""}, True)
        self.assertFalse(return_value)
        return_value = funct("90", {"90f": "No"}, True)
        self.assertFalse(return_value)
        return_value = funct("90", {"90f": "Yes"}, False)
        self.assertTrue(return_value)

    def test_aggregate_weekly_changes(self):
        """
        question_id 90w weekly changes question; aggregates to 90.

        """
        _, funct = MWSSTransformer.ops()["90"]
        return_value = funct("90", {"90w": ""}, True)
        self.assertFalse(return_value)
        return_value = funct("90", {"90w": "No"}, True)
        self.assertFalse(return_value)
        return_value = funct("90", {"90w": "Yes"}, False)
        self.assertTrue(return_value)

    def test_aggregate_fourweekly_changes(self):
        """
        question_id 190w4 used for fourweekly changes question; aggregates to 190.

        """
        _, funct = MWSSTransformer.ops()["190"]
        return_value = funct("190", {"190w4": ""}, True)
        self.assertFalse(return_value)
        return_value = funct("190", {"190w4": "No"}, True)
        self.assertFalse(return_value)
        return_value = funct("190", {"190w4": "Yes"}, False)
        self.assertTrue(return_value)

    def test_aggregate_fourweekly_increase(self):
        """
        Increase in fourweekly pay (200w4); aggregated with monthly increase (200).

        """
        _, funct = MWSSTransformer.ops()["200"]
        return_value = funct("200", {"200w4": "6.0"}, 0)
        self.assertEqual(True, return_value)
        return_value = funct("200", {"200": "7.0", "200w4": "6.0"}, 0)
        self.assertEqual(True, return_value)  # Integer default
        return_value = funct("200", {"200": "7.0", "200w4": "6.0"}, 0.0)
        self.assertEqual(True, return_value)  # Float default

    def test_aggregate_fourweekly_increase_date(self):
        """
        Date of increase in fourweekly pay (210w4); aggregated with monthly (210).

        """
        _, funct = MWSSTransformer.ops()["210"]
        return_value = funct(
            "210", {"210": "2017-01-09", "210w4": "2017-01-11"}, datetime.date.today(),
        )
        self.assertEqual(9, return_value[0].day)
        self.assertEqual(11, return_value[1].day)

    def test_aggregate_fourweekly_increase_employees(self):
        """
        Employees with increase in fourweekly pay (220w4);
        aggregated with monthly increase (220).

        """
        _, funct = MWSSTransformer.ops()["220"]
        return_value = funct("220", {"220w4": "60"}, 0)
        self.assertEqual(60, return_value)
        return_value = funct("220", {"220": "40", "220w4": "41"}, 0)
        self.assertEqual(40, return_value)  # Integer default
        return_value = funct("220", {"220": "40", "220w4": "41"}, 0.0)
        self.assertEqual(40.5, return_value)  # Float default

    def test_aggregate_monthly_changes(self):
        """
        question_id 190m used for monthly changes question; aggregates to 190.

        """
        _, funct = MWSSTransformer.ops()["190"]
        return_value = funct("190", {"190m": ""}, True)
        self.assertFalse(return_value)
        return_value = funct("190", {"190m": "No"}, True)
        self.assertFalse(return_value)
        return_value = funct("190", {"190m": "Yes"}, False)
        self.assertTrue(return_value)

    def test_aggregate_weekly_comments(self):
        """
        question_id 300w, 300f, 300m, 300w4 & 300w5; all aggregated as 300.

        """
        _, funct = MWSSTransformer.ops()["300"]
        for question_id in ("300w", "300f", "300m", "300w4", "300w5"):
            with self.subTest(question_id=question_id):
                return_value = funct("300", {question_id: "Single comment"}, "")
                self.assertEqual("Single comment", return_value)
                return_value = funct("300", {"300": "First comment", question_id: "Second comment"}, "")
                self.assertEqual(["First comment", "Second comment"], return_value.splitlines())

    def test_aggregate_monthly_paid_employees(self):
        """
        question_id 140m, 140w4, 140w5 are added to give a value for monthly paid employees (140).

        """
        _, funct = MWSSTransformer.ops()["140"]
        return_value = funct("140", {"140w4": "125000"}, 0)
        self.assertEqual(125000, return_value)
        for question_id in ("140m", "140w4", "140w5"):
            return_value = funct("140", {"140": "125000", question_id: "25000"}, 0)
            self.assertEqual(150000, return_value)

    def test_aggregate_fiveweekly_changes(self):
        """
        question_id 190w5 used for fiveweekly changes question; aggregates to 190.

        """
        _, funct = MWSSTransformer.ops()["190"]
        return_value = funct("190", {"190w5": ""}, True)
        self.assertFalse(return_value)
        return_value = funct("190", {"190w5": "No"}, True)
        self.assertFalse(return_value)
        return_value = funct("190", {"190w5": "Yes"}, False)
        self.assertTrue(return_value)

    def test_aggregate_fiveweekly_increase(self):
        """
        Increase in fiveweekly pay (200w5); aggregated with monthly increase (200).

        """
        _, funct = MWSSTransformer.ops()["200"]
        return_value = funct("200", {"200w5": "6.0"}, 0)
        self.assertEqual(True, return_value)
        return_value = funct("200", {"200w4": "7.0"}, 0)
        self.assertEqual(True, return_value)
        return_value = funct("200", {"200w4": "7.0"}, 0.0)
        self.assertEqual(True, return_value)
        return_value = funct("200", {"200w4": ""}, 0.0)
        self.assertEqual(False, return_value)

    def test_aggregate_fiveweekly_increase_date(self):
        """
        Date of increase in fiveweekly pay (210w5); aggregated with monthly (210).

        """
        _, funct = MWSSTransformer.ops()["210"]
        return_value = funct(
            "210", {"210": "2017-01-09", "210w5": "2017-01-11"}, datetime.date.today(),
        )
        self.assertEqual(9, return_value[0].day)
        self.assertEqual(11, return_value[1].day)

    def test_aggregate_fiveweekly_increase_employees(self):
        """
        Employees with increase in fiveweekly pay (220w5);
        aggregated with monthly increase (220).

        """
        _, funct = MWSSTransformer.ops()["220"]
        return_value = funct("220", {"220w5": "60"}, 0)
        self.assertEqual(60, return_value)
        return_value = funct("220", {"220": "40", "220w5": "41"}, 0)
        self.assertEqual(40, return_value)  # Integer default
        return_value = funct("220", {"220": "40", "220w5": "41"}, 0.0)
        self.assertEqual(40.5, return_value)  # Float default

    def test_gross_calendar_pay(self):
        """
        Total gross calendar monthly pay

        """
        _, funct = MWSSTransformer.ops()["151"]
        return_value = funct("151", {"151": "1600"}, 0)
        self.assertEqual(1600, return_value)
        return_value = funct("151", {"151": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("151", {"151": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("151", {"151": "-19200.49"}, 0)
        self.assertEqual(0, return_value)

        _, funct = MWSSTransformer.ops()["152"]
        return_value = funct("152", {"152": "1600"}, 0)
        self.assertEqual(1600, return_value)
        return_value = funct("152", {"152": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("152", {"152": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("152", {"152": "-19200.49"}, 0)
        self.assertEqual(0, return_value)

        _, funct = MWSSTransformer.ops()["153"]
        return_value = funct("153", {"153": "1600"}, 0)
        self.assertEqual(1600, return_value)
        return_value = funct("153", {"153": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("153", {"153": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("153", {"153": "-19200.49"}, 0)
        self.assertEqual(0, return_value)

    def test_pay_owing_to_awards(self):
        """
        Breakdown of the calendar monthly paid employees totals.

        """
        _, funct = MWSSTransformer.ops()["171"]
        return_value = funct("171", {"171": "1600"}, 0)
        self.assertEqual(1600, return_value)
        return_value = funct("171", {"171": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("171", {"171": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("171", {"171": "-19200.49"}, 0)
        self.assertEqual(0, return_value)

        _, funct = MWSSTransformer.ops()["172"]
        return_value = funct("172", {"172": "1600"}, 0)
        self.assertEqual(1600, return_value)
        return_value = funct("172", {"172": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("172", {"172": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("172", {"172": "-19200.49"}, 0)
        self.assertEqual(0, return_value)

        _, funct = MWSSTransformer.ops()["173"]
        return_value = funct("173", {"173": "1600"}, 0)
        self.assertEqual(1600, return_value)
        return_value = funct("173", {"173": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("173", {"173": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("173", {"173": "-19200.49"}, 0)
        self.assertEqual(0, return_value)

    def test_pay_bonus_commission_annual_profit(self):
        """
        Breakdown of the calendar monthly paid employees totals.

        """
        _, funct = MWSSTransformer.ops()["181"]
        return_value = funct("181", {"181": "1600"}, 0)
        self.assertEqual(1600, return_value)
        return_value = funct("181", {"181": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("181", {"181": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("181", {"181": "-19200.49"}, 0)
        self.assertEqual(0, return_value)

        _, funct = MWSSTransformer.ops()["182"]
        return_value = funct("182", {"182": "1600"}, 0)
        self.assertEqual(1600, return_value)
        return_value = funct("182", {"182": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("182", {"182": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("182", {"182": "-19200.49"}, 0)
        self.assertEqual(0, return_value)

        _, funct = MWSSTransformer.ops()["173"]
        return_value = funct("173", {"173": "1600"}, 0)
        self.assertEqual(1600, return_value)
        return_value = funct("173", {"173": "19200.49"}, 0)
        self.assertEqual(19200, return_value)
        return_value = funct("173", {"173": "19200.5"}, 0)
        self.assertEqual(19201, return_value)
        return_value = funct("173", {"173": "-19200.49"}, 0)
        self.assertEqual(0, return_value)

    def test_percentage_increase_new_pay_rates(self):
        """
        Breakdown of percentage increase pay rates

        """
        _, funct = MWSSTransformer.ops()["200"]
        return_value = funct("200", {"200w5": "1600"}, 0)
        self.assertEqual(True, return_value)
        return_value = funct("200", {"200w5": "19200.49"}, 0)
        self.assertEqual(True, return_value)
        return_value = funct("200", {"200w5": "19200.5"}, 0)
        self.assertEqual(True, return_value)
        return_value = funct("200", {"200w5": "-19200.49"}, 0)
        self.assertEqual(True, return_value)
        return_value = funct("200", {"200w5": ""}, 0)
        self.assertEqual(False, return_value)

        _, funct = MWSSTransformer.ops()["200"]
        return_value = funct("200", {"200w4": "1600"}, 0)
        self.assertEqual(True, return_value)
        return_value = funct("200", {"200w4": "19200.49"}, 0)
        self.assertEqual(True, return_value)
        return_value = funct("200", {"200w4": "19200.5"}, 0)
        self.assertEqual(True, return_value)
        return_value = funct("200", {"200w4": "-19200.49"}, 0)
        self.assertEqual(True, return_value)
        return_value = funct("200", {"200w5": ""}, 0)
        self.assertEqual(False, return_value)


class TransformTests(unittest.TestCase):

    def test_defaults_empty(self):
        """
        Tests default values are empty

        """
        return_value = MWSSTransformer.transform({})
        self.assertIsInstance(return_value, OrderedDict)
        self.assertEqual([str(i) for i in (130, 131, 132)], list(return_value.keys()))

    def test_defaults_with_data(self):
        """
        Tests default values are populated

        """
        return_value = MWSSTransformer.transform({"40": "33"})
        self.assertIsInstance(return_value, OrderedDict)
        self.assertEqual(33, return_value["40"])
        self.assertEqual(4, len(return_value))

    def test_unsigned(self):
        """
        Test unsigned integer value

        """
        return_value = MWSSTransformer.transform({"40": "33"})
        self.assertEqual(33, return_value["40"])
        item = CSFormatter._pck_item("40", return_value["40"])
        self.assertEqual(item, "0040 00000000033")

    def test_unsigned_decimals(self):
        """
        Test unsigned decimal value

        """
        digits_ingested_as_bools = [100, 200]
        for question_range in digits_ingested_as_bools:
            question_id = str(question_range)
            with self.subTest(question_range=question_range, question_id=question_id):
                return_value = MWSSTransformer.transform({question_id: "64.0"})
                self.assertIs(True, return_value[question_id])
                self.assertEqual(1, CSFormatter._pck_value(return_value[question_id]))

    def test_currency(self):
        """
        Test currency value

        """
        return_value = MWSSTransformer.transform({"50": "36852"})
        self.assertEqual(36852, return_value["50"])
        item = CSFormatter._pck_item("50", return_value["50"])
        self.assertEqual(item, "0050 00000036852")

    def test_digits_to_onetwo(self):
        """
        Test question value in question range return as boolean

        """
        digits_ingested_as_bools = [100, 120, 200, 220]
        for question_range in digits_ingested_as_bools:
            question_id = str(question_range)
            with self.subTest(question_range=question_range, question_id=question_id):
                return_value = MWSSTransformer.transform({question_id: "64"})
                self.assertIs(True, return_value[question_id])
                self.assertEqual(1, CSFormatter._pck_value(return_value[question_id]))
                return_value = MWSSTransformer.transform({question_id: ""})
                self.assertEqual(2, CSFormatter._pck_value(return_value[question_id]))

    def test_pay_frequency_as_bool(self):
        """
        Test pay frequency value in question range returns as boolean

        """
        pay_frequencies = {
            130: "Calendar monthly",
            131: "Four weekly",
            132: "Five weekly",
        }
        for question_id, return_value in pay_frequencies.items():
            question_id = str(question_id)
            with self.subTest(question_id=question_id, return_value=return_value):
                return_value = MWSSTransformer.transform({question_id: return_value})
                self.assertIs(True, return_value[question_id])
                self.assertEqual(1, CSFormatter._pck_value(return_value[question_id]))
                return_value = MWSSTransformer.transform({question_id: ""})
                self.assertIs(False, return_value[question_id])
                self.assertEqual(2, CSFormatter._pck_value(return_value[question_id]))
                return_value = MWSSTransformer.transform({})
                self.assertIs(False, return_value[question_id])
                self.assertEqual(2, CSFormatter._pck_value(return_value[question_id]))

    def test_dates_to_onetwo(self):
        """
        Test dates in question range are returned as boolean

        """
        dates_ingested_as_bools = [110, 210]
        for question_range in dates_ingested_as_bools:
            question_id = str(question_range)
            with self.subTest(question_range=question_range, question_id=question_id):
                return_value = MWSSTransformer.transform({question_id: "23/4/2017"})
                self.assertEqual([datetime.date(2017, 4, 23)], return_value[question_id])
                self.assertEqual(1, CSFormatter._pck_value(return_value[question_id]))
                return_value = MWSSTransformer.transform({question_id: ""})
                self.assertEqual([], return_value[question_id])
                self.assertEqual(2, CSFormatter._pck_value(return_value[question_id]))

    def test_aggregate_fourweekly_changes(self):
        """
        question_id 190w4 used for fourweekly changes question; aggregates to 190.

        """
        return_value = MWSSTransformer.transform({"190w4": ""})
        self.assertIs(False, return_value["190"])
        return_value = MWSSTransformer.transform({"190w4": "No"})
        self.assertIs(False, return_value["190"])
        return_value = MWSSTransformer.transform({"190w4": "Yes"})
        self.assertIs(True, return_value["190"])

    def test_aggregate_fourweekly_increase(self):
        """
        Increase in fourweekly pay (200w4); aggregated with monthly increase (200).

        """
        return_value = MWSSTransformer.transform({"200w4": "25"})
        self.assertIs(True, return_value["200"])

    def test_aggregate_fourweekly_increase_date(self):
        """
        Date of increase in fourweekly pay (210w4); aggregated with monthly (210).

        """
        return_value = MWSSTransformer.transform({"210w4": "2017-01-11"})
        self.assertEqual(1, len(return_value["210"]))
        self.assertEqual(11, return_value["210"][0].day)
        self.assertEqual(1, return_value["210"][0].month)

    def test_aggregate_fourweekly_increase_employees(self):
        """
        Employees with increase in fourweekly pay (220w4);
        aggregated with monthly increase (220).

        """
        return_value = MWSSTransformer.transform({"220w4": "25"})
        self.assertIs(True, return_value["220"])

    def test_aggregate_monthly_changes(self):
        """
        question_id 190m used for monthly changes question; aggregates to 190.

        """
        return_value = MWSSTransformer.transform({"190m": ""})
        self.assertFalse(return_value["190"])
        return_value = MWSSTransformer.transform({"190m": "No"})
        self.assertFalse(return_value["190"])
        return_value = MWSSTransformer.transform({"190m": "Yes"})
        self.assertTrue(return_value["190"])

    def test_aggregate_weekly_comments(self):
        """
        question_id 300w, 300f, 300m, 300w4 & 300w5; all aggregated as 300.

        """
        for question_id in ("300w", "300f", "300m", "300w4", "300w5"):
            with self.subTest(question_id=question_id):
                return_value = MWSSTransformer.transform({question_id: "This is a comment"})
                self.assertEqual(True, return_value["300"])
                self.assertEqual(4, len(return_value))

    def test_aggregate_monthly_paid_employees(self):
        """
        question_id 140m, 140w4, 140w5 are added to give a value for monthly paid employees (140).

        """
        for question_id in ("140m", "140w4", "140w5"):
            with self.subTest(question_id=question_id):
                return_value = MWSSTransformer.transform({question_id: "25"})
                self.assertEqual(25, return_value["140"])
                self.assertEqual(4, len(return_value))

    def test_aggregate_fiveweekly_changes(self):
        """
        question_id 190w5 used for fiveweekly changes question; aggregates to 190.

        """
        return_value = MWSSTransformer.transform({"190w5": ""})
        self.assertFalse(return_value["190"])
        return_value = MWSSTransformer.transform({"190w5": "No"})
        self.assertFalse(return_value["190"])
        return_value = MWSSTransformer.transform({"190w5": "Yes"})
        self.assertTrue(return_value["190"])

    def test_aggregate_fiveweekly_increase(self):
        """
        Increase in fiveweekly pay (200w5); aggregated with monthly increase (200).

        """
        return_value = MWSSTransformer.transform({"200w5": "25"})
        self.assertIs(True, return_value["200"])

    def test_aggregate_fiveweekly_increase_date(self):
        """
        Date of increase in fiveweekly pay (210w5); aggregated with monthly (210).

        """
        return_value = MWSSTransformer.transform({"210w5": "2017-01-11"})
        self.assertEqual(1, len(return_value["210"]))
        self.assertEqual(11, return_value["210"][0].day)
        self.assertEqual(1, return_value["210"][0].month)

    def test_aggregate_fiveweekly_increase_employees(self):
        """
        Employees with increase in fiveweekly pay (220w5);
        aggregated with monthly increase (220).

        """
        return_value = MWSSTransformer.transform({"220w5": "25"})
        self.assertIs(True, return_value["220"])

    def test_imputed_zero_values_weekly(self):
        """
        Breakdown figures (60, 70, 80) are imputed with zero when the respondent
        has confirmed the total (50) is zero.
        """
        return_value = MWSSTransformer.transform({"d50": "Yes"})
        self.assertEqual(0, return_value["50"])
        self.assertEqual(0, return_value["60"])
        self.assertEqual(0, return_value["70"])
        self.assertEqual(0, return_value["80"])

    def test_imputed_zero_values_fortnightly(self):
        """
        Breakdown figures (60, 70, 80) are imputed with zero when the respondent
        has confirmed the total (50f) is zero.
        """
        return_value = MWSSTransformer.transform({"d50f": "Yes"})
        self.assertEqual(0, return_value["50"])
        self.assertEqual(0, return_value["60"])
        self.assertEqual(0, return_value["70"])
        self.assertEqual(0, return_value["80"])

    def test_imputed_zero_values_weekly_and_fortnightly(self):
        """
        Breakdown figures (60, 70, 80) are imputed with zero when the respondent
        has confirmed the totals (50, 50f) are zero.
        """
        return_value = MWSSTransformer.transform({"d50": "Yes", "d50f": "Yes"})
        self.assertEqual(0, return_value["50"])
        self.assertEqual(0, return_value["60"])
        self.assertEqual(0, return_value["70"])
        self.assertEqual(0, return_value["80"])

    def test_imputed_zero_values_monthly(self):
        """
        Breakdown figures (171, 181) are imputed with zero when the respondent
        has confirmed the total (151) is zero.
        """
        return_value = MWSSTransformer.transform({"d151": "Yes"})
        self.assertEqual(0, return_value["151"])
        self.assertEqual(0, return_value["171"])
        self.assertEqual(0, return_value["181"])

    def test_imputed_zero_values_fourweekly(self):
        """
        Breakdown figures (172, 182) are imputed with zero when the respondent
        has confirmed the total (152) is zero.
        """
        return_value = MWSSTransformer.transform({"d152": "Yes"})
        self.assertEqual(0, return_value["152"])
        self.assertEqual(0, return_value["172"])
        self.assertEqual(0, return_value["182"])

    def test_imputed_zero_values_fiveweekly(self):
        """
        Breakdown figures (173, 183) are imputed with zero when the respondent
        has confirmed the total (153) is zero.
        """
        return_value = MWSSTransformer.transform({"d153": "Yes"})
        self.assertEqual(0, return_value["153"])
        self.assertEqual(0, return_value["173"])
        self.assertEqual(0, return_value["183"])


class BatchFileTests(unittest.TestCase):

    replies_dir = 'tests/replies/'

    def test_pck_form_header(self):
        """
        Test package form header

        """
        form_id = 5
        ru_ref = 49900001225
        check = "C"
        period = "200911"
        return_value = CSFormatter._pck_form_header(form_id, ru_ref, check, period)
        self.assertEqual("0005:49900001225C:200911", return_value)

    def test_load_survey(self):
        """
        Tests if load data passes if survey id is 134

        """
        ids = Survey.identifiers({
            "survey_id": "134",
            "tx_id": "27923934-62de-475c-bc01-433c09fd38b8",
            "collection": {
                "instrument_id": "0005",
                "period": "201704"
            },
            "metadata": {
                "user_id": "123456789",
                "ru_ref": "12345678901A"
            }
        }, batch_nr=0, seq_nr=0)
        return_value = Survey.load_survey(ids, MWSSTransformer.pattern)
        self.assertIsNotNone(return_value)

    def test_load_survey_miss(self):
        """
        Tests if load data is missed if survey id is not 134

        """
        ids = Survey.identifiers({
            "survey_id": "127",
            "tx_id": "27923934-62de-475c-bc01-433c09fd38b8",
            "collection": {
                "instrument_id": "0001",
                "period": "201704"
            },
            "metadata": {
                "user_id": "123456789",
                "ru_ref": "12345678901A"
            }
        }, batch_nr=0, seq_nr=0)

        with pytest.raises(MissingSurveyException):
            Survey.load_survey(ids, MWSSTransformer.pattern)

    def test_pck_lines(self):
        """
        Tests data in packet is valid

        """
        inst_id = "0005"
        ru_ref = 49900001225
        check = "C"
        period = "200911"
        data = OrderedDict([
            ("0001", 2),
            ("0140", 124),
            ("0151", 217222)
        ])
        self.assertTrue(isinstance(return_value, int) for return_value in data.values())
        return_value = CSFormatter._pck_lines(data, inst_id, ru_ref, check, period)
        self.assertEqual([
            "FV          ",
            "0005:49900001225C:200911",
            "0001 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], return_value)

    def test_idbr_receipt(self):
        """
        Tests inter-departmental business register receipt

        """
        f = open(self.replies_dir + "eq-mwss.json", "r")
        reply = json.loads(f.read())
        f.close()
        reply["tx_id"] = "27923934-62de-475c-bc01-433c09fd38b8"
        ids = Survey.identifiers(reply, batch_nr=3866, seq_nr=0)
        id_dict = ids._asdict()

        return_value = CSFormatter._idbr_receipt(id_dict["survey_id"], id_dict["ru_ref"], id_dict["ru_check"],
                                                 id_dict["period"])
        self.assertEqual("12346789012:A:134:201605", return_value)

    def test_identifiers(self):
        """
        Tests identifiers are valid

        """
        f = open(self.replies_dir + "eq-mwss.json", "r")
        reply = json.loads(f.read())
        f.close()
        reply["tx_id"] = "27923934-62de-475c-bc01-433c09fd38b8"
        reply["collection"]["period"] = "200911"
        ids = Survey.identifiers(reply, batch_nr=0, seq_nr=0)
        self.assertIsInstance(ids, Survey.Identifiers)
        self.assertEqual(0, ids.batch_nr)
        self.assertEqual(0, ids.seq_nr)
        self.assertEqual(reply["tx_id"], ids.tx_id)
        self.assertEqual(datetime.date.today(), ids.ts.date())
        self.assertEqual("134", ids.survey_id)
        self.assertEqual("K5O86M2NU1", ids.user_id)
        self.assertEqual("12346789012", ids.ru_ref)
        self.assertEqual("A", ids.ru_check)
        self.assertEqual("200911", ids.period)

    def test_pck_from_untransformed_data(self):
        """
        Test package from untransformed data is correct

        """
        f = open(self.replies_dir + "eq-mwss.json", "r")
        reply = json.loads(f.read())
        f.close()
        reply["tx_id"] = "27923934-62de-475c-bc01-433c09fd38b8"
        reply["survey_id"] = "134"
        reply["collection"]["period"] = "200911"
        reply["metadata"]["ru_ref"] = "49900001225C"
        reply["data"] = OrderedDict([
            ("0001", 2),
            ("0140", 124),
            ("0151", 217222)
        ])
        ids = Survey.identifiers(reply, batch_nr=3866, seq_nr=0)
        id_dict = ids._asdict()
        return_value = CSFormatter._pck_lines(reply["data"], id_dict["inst_id"], id_dict["ru_ref"], id_dict["ru_check"],
                                              id_dict["period"])
        self.assertEqual([
            "FV          ",
            "0005:49900001225C:200911",
            "0001 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], return_value)

    def test_pck_from_transformed_data(self):
        """
        Test package from transformer returned data correctly

        """
        f = open(self.replies_dir + "eq-mwss.json", "r")
        reply = json.loads(f.read())
        f.close()
        reply["tx_id"] = "27923934-62de-475c-bc01-433c09fd38b8"
        reply["survey_id"] = "134"
        reply["collection"]["period"] = "200911"
        reply["metadata"]["ru_ref"] = "49900001225C"
        ids = Survey.identifiers(reply, batch_nr=3866, seq_nr=0)
        data = MWSSTransformer.transform(
            OrderedDict([
                ("40", 2),
                ("140", 124),
                ("151", 217222)
            ])
        )
        id_dict = ids._asdict()
        return_value = CSFormatter._pck_lines(data, id_dict["inst_id"], id_dict["ru_ref"], id_dict["ru_check"],
                                              id_dict["period"])
        self.assertEqual([
            "FV          ",
            "0005:49900001225C:200911",
            "0040 00000000002",
            "0130 00000000002",
            "0131 00000000002",
            "0132 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], return_value)


class PackingTests(unittest.TestCase):

    def test_requires_ids(self):
        """
        Test requires id user warning

        """
        self.assertRaises(
            MissingIdsException,
            MWSSTransformer,
            {},
            seq_nr=0
        )

    def test_original_response_is_stored(self):
        """Compare the dictionary loaded from the zip file json is the same as that submitted"""
        expected_json_data = {
            "survey_id": "134",
            "tx_id": "27923934-62de-475c-bc01-433c09fd38b8",
            "collection": {
                "instrument_id": "0005",
                "period": "201704"
            },
            "metadata": {
                "user_id": "123456789",
                "ru_ref": "12345678901A"
            },
            "submitted_at": "2017-04-12T13:01:26Z",
            "data": {"something": "some data", "something else": "some other data"}
        }
        seq_nr = 12345

        transformer = get_transformer(expected_json_data, sequence_no=seq_nr)
        result = transformer.get_zip(img_seq=itertools.count())

        z = zipfile.ZipFile(result)
        zfile = z.open('EDC_QJson/134_2792393462de475c.json', 'r')
        actual_json_data = json.loads(zfile.read().decode('utf-8'))
        z.close()

        self.assertEqual(actual_json_data, expected_json_data)
