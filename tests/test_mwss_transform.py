from collections import OrderedDict
import datetime
import itertools
import json
import os.path
import unittest
import zipfile

import pkg_resources

from sdx.common.formats.cs_formatter import CSFormatter
from sdx.common.processor import Processor
from sdx.common.survey import Survey
from sdx.common.test.test_transformer import PackingTests as TransformerTests
from transform.transformers.MWSSTransformer import MWSSTransformer


class SurveyTests(unittest.TestCase):
    def test_datetime_ms_with_colon_in_timezone(self):
        result = Survey.parse_timestamp("2017-01-11T17:18:53.020222+00:00")
        self.assertIsInstance(result, datetime.datetime)

    def test_datetime_ms_with_timezone(self):
        result = Survey.parse_timestamp("2017-01-11T17:18:53.020222+0000")
        self.assertIsInstance(result, datetime.datetime)

    def test_datetime_zulu(self):
        result = Survey.parse_timestamp("2017-01-11T17:18:53Z")
        self.assertIsInstance(result, datetime.datetime)

    def test_date_iso(self):
        result = Survey.parse_timestamp("2017-01-11")
        self.assertNotIsInstance(result, datetime.datetime)
        self.assertIsInstance(result, datetime.date)

    def test_date_diary(self):
        result = Survey.parse_timestamp("11/07/2017")
        self.assertNotIsInstance(result, datetime.datetime)
        self.assertIsInstance(result, datetime.date)


class OpTests(unittest.TestCase):
    def test_processor_unsigned(self):
        proc = Processor.unsigned_integer

        # Supply int default for range checking
        self.assertEqual(0, proc("q", {"q": -1.24}, 0))
        self.assertEqual(0, proc("q", {"q": 0.49}, 0))
        self.assertEqual(1, proc("q", {"q": 1}, 0))
        self.assertEqual(100, proc("q", {"q": 1E2}, 0))
        self.assertEqual(1000000000, proc("q", {"q": 1E9}, 0))

        # Supply bool default for range checking and type coercion
        self.assertIs(False, proc("q", {"q": -1}, False))
        self.assertIs(False, proc("q", {"q": 0}, False))
        self.assertIs(True, proc("q", {"q": 1}, False))
        self.assertIs(True, proc("q", {"q": 1E2}, False))
        self.assertIs(True, proc("q", {"q": 1E9}, False))
        self.assertIs(False, proc("q", {"q": 0}, False))

    def test_processor_percentage(self):
        proc = Processor.percentage

        # Supply int default for range checking
        self.assertEqual(0, proc("q", {"q": -1}, 0))
        self.assertEqual(0, proc("q", {"q": 0}, 0))
        self.assertEqual(100, proc("q", {"q": 100}, 0))
        self.assertEqual(0, proc("q", {"q": 0}, 0))

        # Supply bool default for range checking and type coercion
        self.assertIs(False, proc("q", {"q": -1}, False))
        self.assertIs(False, proc("q", {"q": 0}, False))
        self.assertIs(True, proc("q", {"q": 100}, False))
        self.assertIs(False, proc("q", {"q": 0}, False))

    def test_ops(self):
        response = {
            "survey_id": "134",
            "tx_id": "27923934-62de-475c-bc01-433c09fd38b8",
            "collection": {
                "instrument_id": "0001",
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
        default, fn = MWSSTransformer.ops()["100"]
        result = fn("100", {"100": "6.0"}, 0)
        self.assertEqual(6, result)

    def test_aggregate_weekly_paid_employees(self):
        """
        QIds 40, 40f are added to give a value for weekly paid employees (40).

        """
        default, fn = MWSSTransformer.ops()["40"]
        result = fn("40", {"40": "125000"}, 0)
        self.assertEqual(125000, result)
        result = fn("40", {"40": "125000", "40f": "25000"}, 0)
        self.assertEqual(150000, result)

    def test_aggregate_fortnightly_gross_pay(self):
        """
        Fortnightly gross pay (50f) is divided by 2 and added to
        the value for question_id 50.

        """
        default, fn = MWSSTransformer.ops()["50"]
        result = fn("50", {"50f": "1600"}, 0)
        self.assertEqual(800, result)
        result = fn("50", {"50": "19200", "50f": "1600"}, 0)
        self.assertEqual(20000, result)
        result = fn("50", {"50": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = fn("50", {"50": "19200.5", "50f": "1600.5"}, 0)
        self.assertEqual(20001, result)
        result = fn("50", {"50": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = fn("50", {"50": "19200.02", "50f": "1600.02"}, 0)
        self.assertEqual(20000, result)

    def test_aggregate_fortnightly_bonuses(self):
        """
        Fortnightly holiday pay (60f), arrears of pay (70f) and bonuses (80f)
        are divided by 2 and added to qids 60, 70, 80 respectively.

        """
        default, fn = MWSSTransformer.ops()["60"]
        result = fn("60", {"60f": "360"}, 0)
        self.assertEqual(180, result)
        result = fn("60", {"60": "4600", "60f": "360"}, 0)
        self.assertEqual(4780, result)
        result = fn("60", {"60": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = fn("60", {"60": "19200.5", "60f": "1600.5"}, 0)
        self.assertEqual(20001, result)
        result = fn("60", {"60": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = fn("60", {"60": "19200.02", "60f": "1600.02"}, 0)
        self.assertEqual(20000, result)

        default, fn = MWSSTransformer.ops()["70"]
        result = fn("70", {"70f": "1280"}, 0)
        self.assertEqual(640, result)
        result = fn("70", {"70": "7360", "70f": "1280"}, 0)
        self.assertEqual(8000, result)
        result = fn("70", {"70": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = fn("70", {"70": "19200.5", "70f": "1600.5"}, 0)
        self.assertEqual(20001, result)
        result = fn("70", {"70": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = fn("70", {"70": "19200.02", "70f": "1600.02"}, 0)
        self.assertEqual(20000, result)

        default, fn = MWSSTransformer.ops()["80"]
        result = fn("80", {"80f": "5000"}, 0)
        self.assertEqual(2500, result)
        result = fn("80", {"80": "15000", "80f": "5000"}, 0)
        self.assertEqual(17500, result)
        result = fn("80", {"80": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = fn("80", {"80": "19200.5", "80f": "1600.5"}, 0)
        self.assertEqual(20001, result)
        result = fn("80", {"80": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = fn("80", {"80": "19200.02", "80f": "1600.02"}, 0)
        self.assertEqual(20000, result)

    def test_aggregate_fortnightly_increase(self):
        """
        Increase in Fortnightly pay (100f); aggregated with weekly increase (100).

        """
        default, fn = MWSSTransformer.ops()["100"]
        result = fn("100", {"100f": "6.0"}, 0)
        self.assertEqual(6, result)
        result = fn("100", {"100": "7.0", "100f": "6.0"}, 0)
        self.assertEqual(6, result)  # Integer default
        result = fn("100", {"100": "7.0", "100f": "6.0"}, 0.0)
        self.assertEqual(6.5, result)  # Float default

    def test_aggregate_fortnightly_increase_date(self):
        """
        Date of increase in Fortnightly pay (110f); aggregated with weekly (110).

        """
        default, fn = MWSSTransformer.ops()["110"]
        result = fn(
            "110", {"110": "2017-01-09", "110f": "2017-01-11"}, datetime.date.today(),
        )
        self.assertEqual(9, result[0].day)
        self.assertEqual(11, result[1].day)

    def test_aggregate_fortnightly_increase_employees(self):
        """
        Employees with increase in Fortnightly pay (120f);
        aggregated with weekly increase (120).

        """
        default, fn = MWSSTransformer.ops()["120"]
        result = fn("120", {"120f": "60"}, 0)
        self.assertEqual(60, result)
        result = fn("120", {"120": "40", "120f": "41"}, 0)
        self.assertEqual(40, result)  # Integer default
        result = fn("120", {"120": "40", "120f": "41"}, 0.0)
        self.assertEqual(40.5, result)  # Float default

    def test_aggregate_fortnightly_changes(self):
        """
        QIds 90f - 97f used for fortnightly changes questions; all aggregated as 90.

        """
        default, fn = MWSSTransformer.ops()["90"]
        for question_id in ("90f", "91f", "92f", "93f", "94f", "95f", "96f", "97f"):
            with self.subTest(question_id=question_id):
                result = fn("90", {question_id: ""}, True)
                self.assertFalse(result)
                result = fn("90", {question_id: "No"}, True)
                self.assertFalse(result)
                result = fn("90", {question_id: "Yes"}, False)
                self.assertTrue(result)

    def test_aggregate_weekly_changes(self):
        """
        QIds 90w - 97w used for weekly changes questions; all aggregated as 90.

        """
        default, fn = MWSSTransformer.ops()["90"]
        for question_id in ("90w", "91w", "92w", "93w", "94w", "95w", "96w", "97w"):
            with self.subTest(question_id=question_id):
                result = fn("90", {question_id: ""}, True)
                self.assertFalse(result)
                result = fn("90", {question_id: "No"}, True)
                self.assertFalse(result)
                result = fn("90", {question_id: "Yes"}, False)
                self.assertTrue(result)

    def test_radio_button_logic(self):
        """
        QIds 92w, 94w, 92f, 94f, 192m, 194m, 192w4, 194w4, 192w5, 194w5
        have answers other than Yes/No.

        """
        default, fn = MWSSTransformer.ops()["90"]
        for question_id in ("92w", "94w", "92f", "94f"):
            with self.subTest(question_id=question_id):
                result = fn("90", {question_id: ""}, True)
                self.assertFalse(result)
                result = fn("90", {question_id: "No significant change"}, True)
                self.assertFalse(result)
                result = fn("90", {question_id: "Any other string"}, False)
                self.assertTrue(result)

        default, fn = MWSSTransformer.ops()["190"]
        for question_id in ("192m", "194m", "192w4", "194w4", "192w5", "194w5"):
            with self.subTest(question_id=question_id):
                result = fn("190", {question_id: ""}, True)
                self.assertFalse(result)
                result = fn("190", {question_id: "No significant change"}, True)
                self.assertFalse(result)
                result = fn("190", {question_id: "Any other string"}, False)
                self.assertTrue(result)

    def test_aggregate_fourweekly_changes(self):
        """
        QIds 190w4 - 197w4 used for fourweekly changes questions; all aggregated as 190.

        """
        default, fn = MWSSTransformer.ops()["190"]
        for question_id in ("190w4", "191w4", "192w4", "193w4", "194w4", "195w4", "196w4", "197w4"):
            with self.subTest(question_id=question_id):
                result = fn("190", {question_id: ""}, True)
                self.assertFalse(result)
                result = fn("190", {question_id: "No"}, True)
                self.assertFalse(result)
                result = fn("190", {question_id: "Yes"}, False)
                self.assertTrue(result)

    def test_aggregate_fourweekly_increase(self):
        """
        Increase in fourweekly pay (200w4); aggregated with monthly increase (200).

        """
        default, fn = MWSSTransformer.ops()["200"]
        result = fn("200", {"200w4": "6.0"}, 0)
        self.assertEqual(True, result)
        result = fn("200", {"200": "7.0", "200w4": "6.0"}, 0)
        self.assertEqual(True, result)  # Integer default
        result = fn("200", {"200": "7.0", "200w4": "6.0"}, 0.0)
        self.assertEqual(True, result)  # Float default

    def test_aggregate_fourweekly_increase_date(self):
        """
        Date of increase in fourweekly pay (210w4); aggregated with monthly (210).

        """
        default, fn = MWSSTransformer.ops()["210"]
        result = fn(
            "210", {"210": "2017-01-09", "210w4": "2017-01-11"}, datetime.date.today(),
        )
        self.assertEqual(9, result[0].day)
        self.assertEqual(11, result[1].day)

    def test_aggregate_fourweekly_increase_employees(self):
        """
        Employees with increase in fourweekly pay (220w4);
        aggregated with monthly increase (220).

        """
        default, fn = MWSSTransformer.ops()["220"]
        result = fn("220", {"220w4": "60"}, 0)
        self.assertEqual(60, result)
        result = fn("220", {"220": "40", "220w4": "41"}, 0)
        self.assertEqual(40, result)  # Integer default
        result = fn("220", {"220": "40", "220w4": "41"}, 0.0)
        self.assertEqual(40.5, result)  # Float default

    def test_aggregate_monthly_changes(self):
        """
        QIds 190m - 197m used for monthly changes questions; all aggregated as 190.

        """
        default, fn = MWSSTransformer.ops()["190"]
        for question_id in ("190m", "191m", "192m", "193m", "194m", "195m", "196m", "197m"):
            with self.subTest(question_id=question_id):
                result = fn("190", {question_id: ""}, True)
                self.assertFalse(result)
                result = fn("190", {question_id: "No"}, True)
                self.assertFalse(result)
                result = fn("190", {question_id: "Yes"}, False)
                self.assertTrue(result)

    def test_aggregate_weekly_comments(self):
        """
        QIds 300w, 300f, 300m, 300w4 & 300w5; all aggregated as 300.

        """
        default, fn = MWSSTransformer.ops()["300"]
        for question_id in ("300w", "300f", "300m", "300w4", "300w5"):
            with self.subTest(question_id=question_id):
                result = fn("300", {question_id: "Single comment"}, "")
                self.assertEqual("Single comment", result)
                result = fn("300", {"300": "First comment", question_id: "Second comment"}, "")
                self.assertEqual(["First comment", "Second comment"], result.splitlines())

    def test_aggregate_monthly_paid_employees(self):
        """
        QIds 140m, 140w4, 140w5 are added to give a value for monthly paid employees (140).

        """
        default, fn = MWSSTransformer.ops()["140"]
        result = fn("140", {"140w4": "125000"}, 0)
        self.assertEqual(125000, result)
        for question_id in ("140m", "140w4", "140w5"):
            result = fn("140", {"140": "125000", question_id: "25000"}, 0)
            self.assertEqual(150000, result)

    def test_aggregate_fiveweekly_changes(self):
        """
        QIds 190w5 - 197w5 used for fiveweekly changes questions; all aggregated as 190.

        """
        default, fn = MWSSTransformer.ops()["190"]
        for question_id in ("190w5", "191w5", "192w5", "193w5", "194w5", "195w5", "196w5", "197w5"):
            with self.subTest(question_id=question_id):
                result = fn("190", {question_id: ""}, True)
                self.assertFalse(result)
                result = fn("190", {question_id: "No"}, True)
                self.assertFalse(result)
                result = fn("190", {question_id: "Yes"}, False)
                self.assertTrue(result)

    def test_aggregate_fiveweekly_increase(self):
        """
        Increase in fiveweekly pay (200w5); aggregated with monthly increase (200).

        """
        default, fn = MWSSTransformer.ops()["200"]
        result = fn("200", {"200w5": "6.0"}, 0)
        self.assertEqual(True, result)
        result = fn("200", {"200w4": "7.0"}, 0)
        self.assertEqual(True, result)
        result = fn("200", {"200w4": "7.0"}, 0.0)
        self.assertEqual(True, result)
        result = fn("200", {"200w4": ""}, 0.0)
        self.assertEqual(False, result)

    def test_aggregate_fiveweekly_increase_date(self):
        """
        Date of increase in fiveweekly pay (210w5); aggregated with monthly (210).

        """
        default, fn = MWSSTransformer.ops()["210"]
        result = fn(
            "210", {"210": "2017-01-09", "210w5": "2017-01-11"}, datetime.date.today(),
        )
        self.assertEqual(9, result[0].day)
        self.assertEqual(11, result[1].day)

    def test_aggregate_fiveweekly_increase_employees(self):
        """
        Employees with increase in fiveweekly pay (220w5);
        aggregated with monthly increase (220).

        """
        default, fn = MWSSTransformer.ops()["220"]
        result = fn("220", {"220w5": "60"}, 0)
        self.assertEqual(60, result)
        result = fn("220", {"220": "40", "220w5": "41"}, 0)
        self.assertEqual(40, result)  # Integer default
        result = fn("220", {"220": "40", "220w5": "41"}, 0.0)
        self.assertEqual(40.5, result)  # Float default

    def test_gross_calendar_pay(self):
        """
        Total gross calendar monthly pay

        """
        dflt, fn = MWSSTransformer.ops()["151"]
        result = fn("151", {"151": "1600"}, 0)
        self.assertEqual(1600, result)
        result = fn("151", {"151": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = fn("151", {"151": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = fn("151", {"151": "-19200.49"}, 0)
        self.assertEqual(0, result)

        dflt, fn = MWSSTransformer.ops()["152"]
        result = fn("152", {"152": "1600"}, 0)
        self.assertEqual(1600, result)
        result = fn("152", {"152": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = fn("152", {"152": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = fn("152", {"152": "-19200.49"}, 0)
        self.assertEqual(0, result)

        dflt, fn = MWSSTransformer.ops()["153"]
        result = fn("153", {"153": "1600"}, 0)
        self.assertEqual(1600, result)
        result = fn("153", {"153": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = fn("153", {"153": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = fn("153", {"153": "-19200.49"}, 0)
        self.assertEqual(0, result)

    def test_pay_owing_to_awards(self):
        """
        Breakdown of the calendar monthly paid employees totals.

        """
        _, funct = MWSSTransformer.ops()["171"]
        result = funct("171", {"171": "1600"}, 0)
        self.assertEqual(1600, result)
        result = funct("171", {"171": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = funct("171", {"171": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = funct("171", {"171": "-19200.49"}, 0)
        self.assertEqual(0, result)

        _, funct = MWSSTransformer.ops()["172"]
        result = funct("172", {"172": "1600"}, 0)
        self.assertEqual(1600, result)
        result = funct("172", {"172": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = funct("172", {"172": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = funct("172", {"172": "-19200.49"}, 0)
        self.assertEqual(0, result)

        _, funct = MWSSTransformer.ops()["173"]
        result = funct("173", {"173": "1600"}, 0)
        self.assertEqual(1600, result)
        result = funct("173", {"173": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = funct("173", {"173": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = funct("173", {"173": "-19200.49"}, 0)
        self.assertEqual(0, result)

    def test_pay_bonus_commission_annual_profit(self):
        """
        Breakdown of the calendar monthly paid employees totals.

        """
        _, funct = MWSSTransformer.ops()["181"]
        result = funct("181", {"181": "1600"}, 0)
        self.assertEqual(1600, result)
        result = funct("181", {"181": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = funct("181", {"181": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = funct("181", {"181": "-19200.49"}, 0)
        self.assertEqual(0, result)

        _, funct = MWSSTransformer.ops()["182"]
        result = funct("182", {"182": "1600"}, 0)
        self.assertEqual(1600, result)
        result = funct("182", {"182": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = funct("182", {"182": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = funct("182", {"182": "-19200.49"}, 0)
        self.assertEqual(0, result)

        _, funct = MWSSTransformer.ops()["173"]
        result = funct("173", {"173": "1600"}, 0)
        self.assertEqual(1600, result)
        result = funct("173", {"173": "19200.49"}, 0)
        self.assertEqual(19200, result)
        result = funct("173", {"173": "19200.5"}, 0)
        self.assertEqual(19201, result)
        result = funct("173", {"173": "-19200.49"}, 0)
        self.assertEqual(0, result)

    def test_percentage_increase_new_pay_rates(self):
        _, funct = MWSSTransformer.ops()["200"]
        result = funct("200", {"200w5": "1600"}, 0)
        self.assertEqual(True, result)
        result = funct("200", {"200w5": "19200.49"}, 0)
        self.assertEqual(True, result)
        result = funct("200", {"200w5": "19200.5"}, 0)
        self.assertEqual(True, result)
        result = funct("200", {"200w5": "-19200.49"}, 0)
        self.assertEqual(True, result)
        result = funct("200", {"200w5": ""}, 0)
        self.assertEqual(False, result)

        _, funct = MWSSTransformer.ops()["200"]
        result = funct("200", {"200w4": "1600"}, 0)
        self.assertEqual(True, result)
        result = funct("200", {"200w4": "19200.49"}, 0)
        self.assertEqual(True, result)
        result = funct("200", {"200w4": "19200.5"}, 0)
        self.assertEqual(True, result)
        result = funct("200", {"200w4": "-19200.49"}, 0)
        self.assertEqual(True, result)
        result = funct("200", {"200w5": ""}, 0)
        self.assertEqual(False, result)


class TransformTests(unittest.TestCase):
    def test_defaults_empty(self):
        result = MWSSTransformer.transform({})
        self.assertIsInstance(result, OrderedDict)
        self.assertEqual([str(i) for i in (130, 131, 132)], list(result.keys()))

    def test_defaults_with_data(self):
        result = MWSSTransformer.transform({"40": "33"})
        self.assertIsInstance(result, OrderedDict)
        self.assertEqual(33, result["40"])
        self.assertEqual(4, len(result))

    def test_unsigned(self):
        result = MWSSTransformer.transform({"40": "33"})
        self.assertEqual(33, result["40"])
        item = CSFormatter.pck_item("40", result["40"])
        self.assertEqual(item, "0040 00000000033")

    def test_unsigned_decimals(self):
        digits_ingested_as_bools = [100, 200]
        for qNr in digits_ingested_as_bools:
            question_id = str(qNr)
            with self.subTest(qNr=qNr, question_id=question_id):
                result = MWSSTransformer.transform({question_id: "64.0"})
                self.assertIs(True, result[question_id])
                self.assertEqual(1, CSFormatter.pck_value(question_id, result[question_id]))

    def test_currency(self):
        result = MWSSTransformer.transform({"50": "36852"})
        self.assertEqual(36852, result["50"])
        item = CSFormatter.pck_item("50", result["50"])
        self.assertEqual(item, "0050 00000036852")

    def test_digits_to_onetwo(self):
        digits_ingested_as_bools = [100, 120, 200, 220]
        for qNr in digits_ingested_as_bools:
            question_id = str(qNr)
            with self.subTest(qNr=qNr, question_id=question_id):
                result = MWSSTransformer.transform({question_id: "64"})
                self.assertIs(True, result[question_id])
                self.assertEqual(1, CSFormatter.pck_value(question_id, result[question_id]))
                result = MWSSTransformer.transform({question_id: ""})
                self.assertEqual(2, CSFormatter.pck_value(question_id, result[question_id]))

    def test_pay_frequency_as_bool(self):
        pay_frequencies = {
            130: "Calendar monthly",
            131: "Four weekly",
            132: "Five weekly",
        }
        for q, result in pay_frequencies.items():
            question_id = str(q)
            with self.subTest(question_id=question_id, result=result):
                result = MWSSTransformer.transform({question_id: result})
                self.assertIs(True, result[question_id])
                self.assertEqual(1, CSFormatter.pck_value(question_id, result[question_id]))
                result = MWSSTransformer.transform({question_id: ""})
                self.assertIs(False, result[question_id])
                self.assertEqual(2, CSFormatter.pck_value(question_id, result[question_id]))
                result = MWSSTransformer.transform({})
                self.assertIs(False, result[question_id])
                self.assertEqual(2, CSFormatter.pck_value(question_id, result[question_id]))

    def test_dates_to_onetwo(self):
        dates_ingested_as_bools = [110, 210]
        for qNr in dates_ingested_as_bools:
            question_id = str(qNr)
            with self.subTest(qNr=qNr, question_id=question_id):
                result = MWSSTransformer.transform({question_id: "23/4/2017"})
                self.assertEqual([datetime.date(2017, 4, 23)], result[question_id])
                self.assertEqual(1, CSFormatter.pck_value(question_id, result[question_id]))
                result = MWSSTransformer.transform({question_id: ""})
                self.assertEqual([], result[question_id])
                self.assertEqual(2, CSFormatter.pck_value(question_id, result[question_id]))

    def test_aggregate_fourweekly_changes(self):
        """
        QIds 190w4 - 197w4 used for fourweekly changes questions; all aggregated as 190.

        """
        for question_id in ("190w4", "191w4", "192w4", "193w4", "194w4", "195w4", "196w4", "197w4"):
            with self.subTest(question_id=question_id):
                result = MWSSTransformer.transform({question_id: ""})
                self.assertIs(False, result["190"])
                result = MWSSTransformer.transform({question_id: "No"})
                self.assertIs(False, result["190"])
                result = MWSSTransformer.transform({question_id: "Yes"})
                self.assertIs(True, result["190"])

    def test_aggregate_fourweekly_increase(self):
        """
        Increase in fourweekly pay (200w4); aggregated with monthly increase (200).

        """
        result = MWSSTransformer.transform({"200w4": "25"})
        self.assertIs(True, result["200"])

    def test_aggregate_fourweekly_increase_date(self):
        """
        Date of increase in fourweekly pay (210w4); aggregated with monthly (210).

        """
        result = MWSSTransformer.transform({"210w4": "2017-01-11"})
        self.assertEqual(1, len(result["210"]))
        self.assertEqual(11, result["210"][0].day)
        self.assertEqual(1, result["210"][0].month)

    def test_aggregate_fourweekly_increase_employees(self):
        """
        Employees with increase in fourweekly pay (220w4);
        aggregated with monthly increase (220).

        """
        result = MWSSTransformer.transform({"220w4": "25"})
        self.assertIs(True, result["220"])

    def test_aggregate_monthly_changes(self):
        """
        QIds 190m - 197m used for monthly changes questions; all aggregated as 190.

        """
        for question_id in ("190m", "191m", "192m", "193m", "194m", "195m", "196m", "197m"):
            with self.subTest(question_id=question_id):
                result = MWSSTransformer.transform({question_id: ""})
                self.assertFalse(result["190"])
                result = MWSSTransformer.transform({question_id: "No"})
                self.assertFalse(result["190"])
                result = MWSSTransformer.transform({question_id: "Yes"})
                self.assertTrue(result["190"])

    def test_aggregate_weekly_comments(self):
        """
        QIds 300w, 300f, 300m, 300w4 & 300w5; all aggregated as 300.

        """
        for question_id in ("300w", "300f", "300m", "300w4", "300w5"):
            with self.subTest(question_id=question_id):
                result = MWSSTransformer.transform({question_id: "This is a comment"})
                self.assertEqual(True, result["300"])
                self.assertEqual(4, len(result))

    def test_aggregate_monthly_paid_employees(self):
        """
        QIds 140m, 140w4, 140w5 are added to give a value for monthly paid employees (140).

        """
        for question_id in ("140m", "140w4", "140w5"):
            with self.subTest(question_id=question_id):
                result = MWSSTransformer.transform({question_id: "25"})
                self.assertEqual(25, result["140"])
                self.assertEqual(4, len(result))

    def test_aggregate_fiveweekly_changes(self):
        """
        QIds 190w5 - 197w5 used for fiveweekly changes questions; all aggregated as 190.

        """
        for question_id in ("190w5", "191w5", "192w5", "193w5", "194w5", "195w5", "196w5", "197w5"):
            with self.subTest(question_id=question_id):
                result = MWSSTransformer.transform({question_id: ""})
                self.assertFalse(result["190"])
                result = MWSSTransformer.transform({question_id: "No"})
                self.assertFalse(result["190"])
                result = MWSSTransformer.transform({question_id: "Yes"})
                self.assertTrue(result["190"])

    def test_aggregate_fiveweekly_increase(self):
        """
        Increase in fiveweekly pay (200w5); aggregated with monthly increase (200).

        """
        result = MWSSTransformer.transform({"200w5": "25"})
        self.assertIs(True, result["200"])

    def test_aggregate_fiveweekly_increase_date(self):
        """
        Date of increase in fiveweekly pay (210w5); aggregated with monthly (210).

        """
        result = MWSSTransformer.transform({"210w5": "2017-01-11"})
        self.assertEqual(1, len(result["210"]))
        self.assertEqual(11, result["210"][0].day)
        self.assertEqual(1, result["210"][0].month)

    def test_aggregate_fiveweekly_increase_employees(self):
        """
        Employees with increase in fiveweekly pay (220w5);
        aggregated with monthly increase (220).

        """
        result = MWSSTransformer.transform({"220w5": "25"})
        self.assertIs(True, result["220"])


class BatchFileTests(unittest.TestCase):
    def test_pck_batch_header(self):
        batch_nr = 3866
        batch_date = datetime.date(2009, 12, 29)
        result = CSFormatter.pck_batch_header(batch_nr, batch_date)
        self.assertEqual("FBFV00386629/12/09", result)

    def test_pck_form_header(self):
        form_id = 5
        ru_ref = 49900001225
        check = "C"
        period = "200911"
        result = CSFormatter.pck_form_header(form_id, ru_ref, check, period)
        self.assertEqual("0005:49900001225C:200911", result)

    def test_load_survey(self):
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
        result = Survey.load_survey(ids, MWSSTransformer.package, MWSSTransformer.pattern)
        self.assertIsNotNone(result)

    def test_load_survey_miss(self):
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
        result = Survey.load_survey(ids, MWSSTransformer.package, MWSSTransformer.pattern)
        self.assertIsNone(result)

    def test_pck_lines(self):
        batch_nr = 3866
        batch_date = datetime.date(2009, 12, 29)
        survey_id = "134"
        inst_id = "0005"
        ru_ref = 49900001225
        check = "C"
        period = "200911"
        data = OrderedDict([
            ("0001", 2),
            ("0140", 124),
            ("0151", 217222)
        ])
        self.assertTrue(isinstance(result, int) for result in data.values())
        result = CSFormatter.pck_lines(
            data, batch_nr, batch_date, survey_id, inst_id, ru_ref, check, period
        )
        self.assertEqual([
            "FV          ",
            "0005:49900001225C:200911",
            "0001 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], result)

    def test_idbr_receipt(self):
        src = pkg_resources.resource_string(__name__, "replies/eq-mwss.json")
        reply = json.loads(src.decode("utf-8"))
        reply["tx_id"] = "27923934-62de-475c-bc01-433c09fd38b8"
        ids = Survey.identifiers(reply, batch_nr=3866, seq_nr=0)
        result = CSFormatter.idbr_receipt(**ids._asdict())
        self.assertEqual("12346789012:A:134:201605", result)

    def test_identifiers(self):
        src = pkg_resources.resource_string(__name__, "replies/eq-mwss.json")
        reply = json.loads(src.decode("utf-8"))
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
        src = pkg_resources.resource_string(__name__, "replies/eq-mwss.json")
        reply = json.loads(src.decode("utf-8"))
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
        result = CSFormatter.pck_lines(reply["data"], **ids._asdict())
        self.assertEqual([
            "FV          ",
            "0005:49900001225C:200911",
            "0001 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], result)

    def test_pck_from_transformed_data(self):
        src = pkg_resources.resource_string(__name__, "replies/eq-mwss.json")
        reply = json.loads(src.decode("utf-8"))
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
        result = CSFormatter.pck_lines(data, **ids._asdict())
        self.assertEqual([
            "FV          ",
            "0005:49900001225C:200911",
            "0040 00000000002",
            "0130 00000000002",
            "0131 00000000002",
            "0132 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], result)


class PackingTests(unittest.TestCase):
    def test_requires_ids(self):
        self.assertRaises(
            UserWarning,
            MWSSTransformer,
            {},
            seq_nr=0
        )

    def test_tempdir(self):
        settings = TransformerTests.Settings(
            "\\\\NP3RVWAPXX370\\SDX_preprod",
            "EDC_QImages"
        )
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
            "data": {}
        }
        transformer = MWSSTransformer(response, 0)
        self.assertEqual(
            "REC1204_0000.DAT",
            CSFormatter.idbr_name(
                **transformer.ids._asdict()
            )
        )
        transformer.pack(settings=settings, img_seq=itertools.count(), tmp=None)

    def test_image_sequence_number(self):
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
            "data": {}
        }
        seq_nr = 12345
        transformer = MWSSTransformer(response, seq_nr=seq_nr)
        zf = zipfile.ZipFile(transformer.pack(img_seq=itertools.count(), settings=TransformerTests.Settings("", ""), tmp=None))
        fn = next(i for i in zf.namelist() if os.path.splitext(i)[1] == ".csv")
        bits = os.path.splitext(fn)[0].split("_")
        self.assertEqual(seq_nr, int(bits[-1]))
