from collections import OrderedDict
import datetime
import itertools
import json
import os.path
import unittest
import zipfile

import pkg_resources

from transform.transformers.MWSSTransformer import CSFormatter
from transform.transformers.MWSSTransformer import MWSSTransformer
from transform.transformers.MWSSTransformer import Processor
from transform.transformers.MWSSTransformer import Survey


class SurveyTests(unittest.TestCase):

    def test_datetime_ms_with_colon_in_timezone(self):
        rv = Survey.parse_timestamp("2017-01-11T17:18:53.020222+00:00")
        self.assertIsInstance(rv, datetime.datetime)

    def test_datetime_ms_with_timezone(self):
        rv = Survey.parse_timestamp("2017-01-11T17:18:53.020222+0000")
        self.assertIsInstance(rv, datetime.datetime)

    def test_datetime_zulu(self):
        rv = Survey.parse_timestamp("2017-01-11T17:18:53Z")
        self.assertIsInstance(rv, datetime.datetime)

    def test_date_iso(self):
        rv = Survey.parse_timestamp("2017-01-11")
        self.assertNotIsInstance(rv, datetime.datetime)
        self.assertIsInstance(rv, datetime.date)

    def test_date_diary(self):
        rv = Survey.parse_timestamp("11/07/2017")
        self.assertNotIsInstance(rv, datetime.datetime)
        self.assertIsInstance(rv, datetime.date)


class OpTests(unittest.TestCase):

    def test_processor_unsigned(self):
        proc = Processor.unsigned_integer

        # Supply int default for range checking
        self.assertEqual(0, proc("q", {"q": -1}, 0))
        self.assertEqual(0, proc("q", {"q": 0}, 0))
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
        tfr = MWSSTransformer(response, 0, 0)
        self.assertTrue(tfr)


class LogicTests(unittest.TestCase):

    def test_weekly_increase(self):
        """
        Increase in weekly pay (100).

        """
        dflt, fn = MWSSTransformer.ops()["100"]
        rv = fn("100", {"100": "6.0"}, 0)
        self.assertEqual(6, rv)

    def test_aggregate_weekly_paid_employees(self):
        """
        QIds 40, 40f are added to give a value for weekly paid employees (40).

        """
        dflt, fn = MWSSTransformer.ops()["40"]
        rv = fn("40", {"40": "125000"}, 0)
        self.assertEqual(125000, rv)
        rv = fn("40", {"40": "125000", "40f": "25000"}, 0)
        self.assertEqual(150000, rv)

    def test_aggregate_fortnightly_gross_pay(self):
        """
        Fortnightly gross pay (50f) is divided by 2 and added to
        the value for qid 50.

        """
        dflt, fn = MWSSTransformer.ops()["50"]
        rv = fn("50", {"50f": "1600"}, 0)
        self.assertEqual(800, rv)
        rv = fn("50", {"50": "19200", "50f": "1600"}, 0)
        self.assertEqual(20000, rv)

    def test_aggregate_fortnightly_bonuses(self):
        """
        Fortnightly holiday pay (60f), arrears of pay (70f) and bonuses (80f)
        are divided by 2 and added to qids 60, 70, 80 respectively.

        """
        dflt, fn = MWSSTransformer.ops()["60"]
        rv = fn("60", {"60f": "360"}, 0)
        self.assertEqual(180, rv)
        rv = fn("60", {"60": "4600", "60f": "360"}, 0)
        self.assertEqual(4780, rv)

        dflt, fn = MWSSTransformer.ops()["70"]
        rv = fn("70", {"70f": "1280"}, 0)
        self.assertEqual(640, rv)
        rv = fn("70", {"70": "7360", "70f": "1280"}, 0)
        self.assertEqual(8000, rv)

        dflt, fn = MWSSTransformer.ops()["80"]
        rv = fn("80", {"80f": "5000"}, 0)
        self.assertEqual(2500, rv)
        rv = fn("80", {"80": "15000", "80f": "5000"}, 0)
        self.assertEqual(17500, rv)

    def test_aggregate_fortnightly_increase(self):
        """
        Increase in Fortnightly pay (100f); aggregated with weekly increase (100).

        """
        dflt, fn = MWSSTransformer.ops()["100"]
        rv = fn("100", {"100f": "6.0"}, 0)
        self.assertEqual(6, rv)
        rv = fn("100", {"100": "7.0", "100f": "6.0"}, 0)
        self.assertEqual(6, rv)  # Integer default
        rv = fn("100", {"100": "7.0", "100f": "6.0"}, 0.0)
        self.assertEqual(6.5, rv)  # Float default

    def test_aggregate_fortnightly_increase_date(self):
        """
        Date of increase in Fortnightly pay (110f); aggregated with weekly (110).

        """
        dflt, fn = MWSSTransformer.ops()["110"]
        rv = fn(
            "110", {"110": "2017-01-09", "110f": "2017-01-11"}, datetime.date.today(),
        )
        self.assertEqual(9, rv[0].day)
        self.assertEqual(11, rv[1].day)

    def test_aggregate_fortnightly_increase_employees(self):
        """
        Employees with increase in Fortnightly pay (120f);
        aggregated with weekly increase (120).

        """
        dflt, fn = MWSSTransformer.ops()["120"]
        rv = fn("120", {"120f": "60"}, 0)
        self.assertEqual(60, rv)
        rv = fn("120", {"120": "40", "120f": "41"}, 0)
        self.assertEqual(40, rv)  # Integer default
        rv = fn("120", {"120": "40", "120f": "41"}, 0.0)
        self.assertEqual(40.5, rv)  # Float default

    def test_aggregate_fortnightly_changes(self):
        """
        QIds 90f - 97f used for fortnightly changes questions; all aggregated as 90.

        """
        dflt, fn = MWSSTransformer.ops()["90"]
        for qid in ("90f", "91f", "92f", "93f", "94f", "95f", "96f", "97f"):
            with self.subTest(qid=qid):
                rv = fn("90", {qid: ""}, True)
                self.assertFalse(rv)
                rv = fn("90", {qid: "No"}, True)
                self.assertFalse(rv)
                rv = fn("90", {qid: "Yes"}, False)
                self.assertTrue(rv)

    def test_aggregate_weekly_changes(self):
        """
        QIds 90w - 97w used for weekly changes questions; all aggregated as 90.

        """
        dflt, fn = MWSSTransformer.ops()["90"]
        for qid in ("90w", "91w", "92w", "93w", "94w", "95w", "96w", "97w"):
            with self.subTest(qid=qid):
                rv = fn("90", {qid: ""}, True)
                self.assertFalse(rv)
                rv = fn("90", {qid: "No"}, True)
                self.assertFalse(rv)
                rv = fn("90", {qid: "Yes"}, False)
                self.assertTrue(rv)

    def test_radio_button_logic(self):
        """
        QIds 92w, 94w, 92f, 94f, 192m, 194m, 192w4, 194w4, 192w5, 194w5
        have answers other than Yes/No.

        """
        dflt, fn = MWSSTransformer.ops()["90"]
        for qid in ("92w", "94w", "92f", "94f"):
            with self.subTest(qid=qid):
                rv = fn("90", {qid: ""}, True)
                self.assertFalse(rv)
                rv = fn("90", {qid: "No significant change"}, True)
                self.assertFalse(rv)
                rv = fn("90", {qid: "Any other string"}, False)
                self.assertTrue(rv)

        dflt, fn = MWSSTransformer.ops()["190"]
        for qid in ("192m", "194m", "192w4", "194w4", "192w5", "194w5"):
            with self.subTest(qid=qid):
                rv = fn("190", {qid: ""}, True)
                self.assertFalse(rv)
                rv = fn("190", {qid: "No significant change"}, True)
                self.assertFalse(rv)
                rv = fn("190", {qid: "Any other string"}, False)
                self.assertTrue(rv)

    def test_aggregate_fourweekly_changes(self):
        """
        QIds 190w4 - 197w4 used for fourweekly changes questions; all aggregated as 190.

        """
        dflt, fn = MWSSTransformer.ops()["190"]
        for qid in ("190w4", "191w4", "192w4", "193w4", "194w4", "195w4", "196w4", "197w4"):
            with self.subTest(qid=qid):
                rv = fn("190", {qid: ""}, True)
                self.assertFalse(rv)
                rv = fn("190", {qid: "No"}, True)
                self.assertFalse(rv)
                rv = fn("190", {qid: "Yes"}, False)
                self.assertTrue(rv)

    def test_aggregate_fourweekly_increase(self):
        """
        Increase in fourweekly pay (200w4); aggregated with monthly increase (200).

        """
        dflt, fn = MWSSTransformer.ops()["200"]
        rv = fn("200", {"200w4": "6.0"}, 0)
        self.assertEqual(6, rv)
        rv = fn("200", {"200": "7.0", "200w4": "6.0"}, 0)
        self.assertEqual(6, rv)  # Integer default
        rv = fn("200", {"200": "7.0", "200w4": "6.0"}, 0.0)
        self.assertEqual(6.5, rv)  # Float default

    def test_aggregate_fourweekly_increase_date(self):
        """
        Date of increase in fourweekly pay (210w4); aggregated with monthly (210).

        """
        dflt, fn = MWSSTransformer.ops()["210"]
        rv = fn(
            "210", {"210": "2017-01-09", "210w4": "2017-01-11"}, datetime.date.today(),
        )
        self.assertEqual(9, rv[0].day)
        self.assertEqual(11, rv[1].day)

    def test_aggregate_fourweekly_increase_employees(self):
        """
        Employees with increase in fourweekly pay (220w4);
        aggregated with monthly increase (220).

        """
        dflt, fn = MWSSTransformer.ops()["220"]
        rv = fn("220", {"220w4": "60"}, 0)
        self.assertEqual(60, rv)
        rv = fn("220", {"220": "40", "220w4": "41"}, 0)
        self.assertEqual(40, rv)  # Integer default
        rv = fn("220", {"220": "40", "220w4": "41"}, 0.0)
        self.assertEqual(40.5, rv)  # Float default

    def test_aggregate_monthly_changes(self):
        """
        QIds 190m - 197m used for monthly changes questions; all aggregated as 190.

        """
        dflt, fn = MWSSTransformer.ops()["190"]
        for qid in ("190m", "191m", "192m", "193m", "194m", "195m", "196m", "197m"):
            with self.subTest(qid=qid):
                rv = fn("190", {qid: ""}, True)
                self.assertFalse(rv)
                rv = fn("190", {qid: "No"}, True)
                self.assertFalse(rv)
                rv = fn("190", {qid: "Yes"}, False)
                self.assertTrue(rv)

    def test_aggregate_weekly_comments(self):
        """
        QIds 300w, 300f, 300m, 300w4 & 300w5; all aggregated as 300.

        """
        dflt, fn = MWSSTransformer.ops()["300"]
        for qid in ("300w", "300f", "300m", "300w4", "300w5"):
            with self.subTest(qid=qid):
                rv = fn("300", {qid: "Single comment"}, "")
                self.assertEqual("Single comment", rv)
                rv = fn("300", {"300": "First comment", qid: "Second comment"}, "")
                self.assertEqual(["First comment", "Second comment"], rv.splitlines())

    def test_aggregate_monthly_paid_employees(self):
        """
        QIds 140m, 140w4, 140w5 are added to give a value for monthly paid employees (140).

        """
        dflt, fn = MWSSTransformer.ops()["140"]
        rv = fn("140", {"140w4": "125000"}, 0)
        self.assertEqual(125000, rv)
        for qid in ("140m", "140w4", "140w5"):
            rv = fn("140", {"140": "125000", qid: "25000"}, 0)
            self.assertEqual(150000, rv)

    def test_aggregate_fiveweekly_changes(self):
        """
        QIds 190w5 - 197w5 used for fiveweekly changes questions; all aggregated as 190.

        """
        dflt, fn = MWSSTransformer.ops()["190"]
        for qid in ("190w5", "191w5", "192w5", "193w5", "194w5", "195w5", "196w5", "197w5"):
            with self.subTest(qid=qid):
                rv = fn("190", {qid: ""}, True)
                self.assertFalse(rv)
                rv = fn("190", {qid: "No"}, True)
                self.assertFalse(rv)
                rv = fn("190", {qid: "Yes"}, False)
                self.assertTrue(rv)

    def test_aggregate_fiveweekly_increase(self):
        """
        Increase in fiveweekly pay (200w5); aggregated with monthly increase (200).

        """
        dflt, fn = MWSSTransformer.ops()["200"]
        rv = fn("200", {"200w5": "6.0"}, 0)
        self.assertEqual(6, rv)
        rv = fn("200", {"200": "7.0", "200w5": "6.0"}, 0)
        self.assertEqual(6, rv)  # Integer default
        rv = fn("200", {"200": "7.0", "200w5": "6.0"}, 0.0)
        self.assertEqual(6.5, rv)  # Float default

    def test_aggregate_fiveweekly_increase_date(self):
        """
        Date of increase in fiveweekly pay (210w5); aggregated with monthly (210).

        """
        dflt, fn = MWSSTransformer.ops()["210"]
        rv = fn(
            "210", {"210": "2017-01-09", "210w5": "2017-01-11"}, datetime.date.today(),
        )
        self.assertEqual(9, rv[0].day)
        self.assertEqual(11, rv[1].day)

    def test_aggregate_fiveweekly_increase_employees(self):
        """
        Employees with increase in fiveweekly pay (220w5);
        aggregated with monthly increase (220).

        """
        dflt, fn = MWSSTransformer.ops()["220"]
        rv = fn("220", {"220w5": "60"}, 0)
        self.assertEqual(60, rv)
        rv = fn("220", {"220": "40", "220w5": "41"}, 0)
        self.assertEqual(40, rv)  # Integer default
        rv = fn("220", {"220": "40", "220w5": "41"}, 0.0)
        self.assertEqual(40.5, rv)  # Float default


class TransformTests(unittest.TestCase):

    def test_no_defaults_empty(self):
        rv = MWSSTransformer.transform({})
        self.assertIsInstance(rv, OrderedDict)
        self.assertFalse(rv)

    def test_no_defaults_with_data(self):
        rv = MWSSTransformer.transform({"40": "33"})
        self.assertIsInstance(rv, OrderedDict)
        self.assertEquals(33, rv["40"])
        self.assertEqual(1, len(rv))

    def test_unsigned(self):
        rv = MWSSTransformer.transform({"40": "33"})
        self.assertEqual(33, rv["40"])
        item = CSFormatter.pck_item("40", rv["40"])
        self.assertEqual(item, "0040 00000000033")

    def test_currency(self):
        rv = MWSSTransformer.transform({"50": "36852"})
        self.assertEqual(36852, rv["50"])
        item = CSFormatter.pck_item("50", rv["50"])
        self.assertEqual(item, "0050 00000036852")

    def test_digits_to_onetwo(self):
        digits_ingested_as_bools = [100, 120, 200, 220]
        for qNr in digits_ingested_as_bools:
            qid = str(qNr)
            with self.subTest(qNr=qNr, qid=qid):
                rv = MWSSTransformer.transform({qid: "64"})
                self.assertIs(True, rv[qid])
                self.assertEqual(1, CSFormatter.pck_value(qid, rv[qid]))
                rv = MWSSTransformer.transform({qid: ""})
                self.assertEqual(2, CSFormatter.pck_value(qid, rv[qid]))

    def test_dates_to_onetwo(self):
        dates_ingested_as_bools = [110, 210]
        for qNr in dates_ingested_as_bools:
            qid = str(qNr)
            with self.subTest(qNr=qNr, qid=qid):
                rv = MWSSTransformer.transform({qid: "23/4/2017"})
                self.assertEqual([datetime.date(2017, 4, 23)], rv[qid])
                self.assertEqual(1, CSFormatter.pck_value(qid, rv[qid]))
                rv = MWSSTransformer.transform({qid: ""})
                self.assertEqual([], rv[qid])
                self.assertEqual(2, CSFormatter.pck_value(qid, rv[qid]))


class BatchFileTests(unittest.TestCase):

    def test_pck_batch_header(self):
        batch_nr = 3866
        batch_date = datetime.date(2009, 12, 29)
        rv = CSFormatter.pck_batch_header(batch_nr, batch_date)
        self.assertEqual("FBFV00386629/12/09", rv)

    def test_pck_form_header(self):
        form_id = 5
        ru_ref = 49900001225
        check = "C"
        period = "200911"
        rv = CSFormatter.pck_form_header(form_id, ru_ref, check, period)
        self.assertEqual("0005:49900001225C:200911", rv)

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
        rv = Survey.load_survey(ids)
        self.assertIsNotNone(rv)

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
        rv = Survey.load_survey(ids)
        self.assertIsNone(rv)

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
        self.assertTrue(isinstance(val, int) for val in data.values())
        rv = CSFormatter.pck_lines(
            data, batch_nr, batch_date, survey_id, inst_id, ru_ref, check, period
        )
        self.assertEqual([
            "FV          ",
            "0005:49900001225C:200911",
            "0001 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], rv)

    def test_idbr_receipt(self):
        src = pkg_resources.resource_string(__name__, "replies/eq-mwss.json")
        reply = json.loads(src.decode("utf-8"))
        reply["tx_id"] = "27923934-62de-475c-bc01-433c09fd38b8"
        ids = Survey.identifiers(reply, batch_nr=3866, seq_nr=0)
        rv = CSFormatter.idbr_receipt(**ids._asdict())
        self.assertEqual("12346789012:A:134:201605", rv)

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

    def test_pck_from_transformed_data(self):
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
        rv = CSFormatter.pck_lines(reply["data"], **ids._asdict())
        self.assertEqual([
            "FV          ",
            "0005:49900001225C:200911",
            "0001 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], rv)

    def test_pck_no_defaults(self):
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
        rv = CSFormatter.pck_lines(data, **ids._asdict())
        self.assertEqual([
            "FV          ",
            "0005:49900001225C:200911",
            "0040 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], rv)


class PackingTests(unittest.TestCase):

    def test_requires_batch_nr(self):
        self.assertRaises(
            TypeError,
            MWSSTransformer,
            {},
            seq_nr=0
        )

    def test_requires_seq_nr(self):
        self.assertRaises(
            TypeError,
            MWSSTransformer,
            {},
            batch_nr=0
        )

    def test_tempdir(self):
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
        tfr = MWSSTransformer(response, 0, 0)
        self.assertEqual(
            "REC1204_0000.DAT",
            CSFormatter.idbr_name(
                **tfr.ids._asdict()
            )
        )
        try:
            tfr.pack(img_seq=itertools.count())
        except KeyError:
            self.fail("TODO: define pages of survey.")

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
        tfr = MWSSTransformer(response, 0, seq_nr=seq_nr)
        zf = zipfile.ZipFile(tfr.pack(img_seq=itertools.count()))
        fn = next(i for i in zf.namelist() if os.path.splitext(i)[1] == ".csv")
        bits = os.path.splitext(fn)[0].split("_")
        self.assertEqual(seq_nr, int(bits[-1]))
