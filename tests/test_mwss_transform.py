from collections import OrderedDict
import datetime
import itertools
import json
import unittest

from transform.transformers.MWSSTransformer import CSFormatter
from transform.transformers.MWSSTransformer import MWSSTransformer
from transform.transformers.MWSSTransformer import Processor
from transform.transformers.MWSSTransformer import Survey

import pkg_resources


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

    def test_processor_diarydate(self):
        proc = Processor.diarydate
        rv = proc("q", {"q": "11/07/2017"}, datetime.date.today())
        self.assertEqual(datetime.date(2017, 7, 11), rv)

    def test_processor_match_type(self):
        proc = Processor.match_type

        # ints and strings
        self.assertEqual(1, proc("q", {"q": "1"}, 0))
        self.assertEqual(0, proc("q", {"q": "NaN"}, 0))
        self.assertEqual("1", proc("q", {"q": 1}, ""))

        # bools and strings
        self.assertEqual(True, proc("q", {"q": "1"}, False))
        self.assertEqual(False, proc("q", {"q": ""}, True))

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
        tfr = MWSSTransformer(response)
        self.failUnless(tfr)


class TransformTests(unittest.TestCase):

    def test_unsigned(self):
        rv = MWSSTransformer.transform({"0040": "33"})
        self.assertEqual(33, rv["0040"])
        item = CSFormatter.pck_item("0040", rv["0040"])
        self.assertEqual(item, "0040 00000000033")

    def test_currency(self):
        rv = MWSSTransformer.transform({"0050": "36852"})
        self.assertEqual(36852, rv["0050"])
        item = CSFormatter.pck_item("0050", rv["0050"])
        self.assertEqual(item, "0050 00000036852")

    def test_digits_to_onetwo(self):
        digitsIngestedAsBools = [100, 120, 200, 220]
        for qNr in digitsIngestedAsBools:
            qId = "{0:04}".format(qNr)
            with self.subTest(qNr=qNr, qId=qId):
                rv = MWSSTransformer.transform({qId: "64"})
                self.assertIs(True, rv[qId])
                self.assertEqual(1, CSFormatter.pck_value(qId, rv[qId]))
                rv = MWSSTransformer.transform({qId: ""})
                self.assertEqual(2, CSFormatter.pck_value(qId, rv[qId]))

    def test_dates_to_onetwo(self):
        datesIngestedAsBools = [110, 210]
        for qNr in datesIngestedAsBools:
            qId = "{0:04}".format(qNr)
            with self.subTest(qNr=qNr, qId=qId):
                rv = MWSSTransformer.transform({qId: "23/4/2017"})
                self.assertIs(True, rv[qId])
                self.assertEqual(1, CSFormatter.pck_value(qId, rv[qId]))
                rv = MWSSTransformer.transform({qId: ""})
                self.assertEqual(2, CSFormatter.pck_value(qId, rv[qId]))


class BatchFileTests(unittest.TestCase):

    def test_pck_batch_header(self):
        batchNr = 3866
        batchDate = datetime.date(2009, 12, 29)
        rv = CSFormatter.pck_batch_header(batchNr, batchDate)
        self.assertEqual("FBFV00386629/12/09", rv)

    def test_pck_form_header(self):
        formId = 4
        ruRef = 49900001225
        check = "C"
        period = "200911"
        rv = CSFormatter.pck_form_header(formId, ruRef, check, period)
        self.assertEqual("0004:49900001225C:200911", rv)

    def test_load_survey(self):
        ids = Survey.identifiers({
            "survey_id": "134",
            "tx_id": "27923934-62de-475c-bc01-433c09fd38b8",
            "collection": {
                "instrument_id": "0001",
                "period": "201704"
            },
            "metadata": {
                "user_id": "123456789",
                "ru_ref": "12345678901A"
            }
        })
        rv = MWSSTransformer.load_survey(ids)
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
        })
        rv = MWSSTransformer.load_survey(ids)
        self.assertIsNone(rv)

    def test_pck_lines(self):
        batchNr = 3866
        batchDate = datetime.date(2009, 12, 29)
        instId = "134"
        ruRef = 49900001225
        check = "C"
        period = "200911"
        data = OrderedDict([
            ("0001", 2),
            ("0140", 124),
            ("0151", 217222)
        ])
        self.assertTrue(isinstance(val, int) for val in data.values())
        rv = CSFormatter.pck_lines(data, batchNr, batchDate, instId, ruRef, check, period)
        self.assertEqual([
            "FBFV00386629/12/09",
            "FV",
            "0004:49900001225C:200911",
            "0001 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], rv)

    def test_idbr_receipt(self):
        # TODO: Get proper response data
        src = pkg_resources.resource_string(__name__, "pck/023.0102.json")
        reply = json.loads(src.decode("utf-8"))
        reply["tx_id"] = "27923934-62de-475c-bc01-433c09fd38b8"
        ids = Survey.identifiers(reply, batchNr=3866)
        rv = CSFormatter.idbr_receipt(**ids._asdict())
        self.assertEqual("12345678901:A:023:1604", rv)

    def test_identifiers(self):
        # TODO: Get proper response data
        src = pkg_resources.resource_string(__name__, "pck/023.0102.json")
        reply = json.loads(src.decode("utf-8"))
        reply["tx_id"] = "27923934-62de-475c-bc01-433c09fd38b8"
        reply["collection"]["period"] = "200911"
        ids = Survey.identifiers(reply)
        self.assertIsInstance(ids, Survey.Identifiers)
        self.assertEqual(0, ids.batchNr)
        self.assertEqual(0, ids.seqNr)
        self.assertEqual(reply["tx_id"], ids.txId)
        self.assertEqual(datetime.date.today(), ids.ts.date())
        self.assertEqual("023", ids.surveyId)
        self.assertEqual("789473423", ids.userId)
        self.assertEqual("12345678901", ids.ruRef)
        self.assertEqual("A", ids.ruChk)
        self.assertEqual("200911", ids.period)

    def test_pck_from_transformed_data(self):
        # TODO: Get proper response data
        src = pkg_resources.resource_string(__name__, "pck/023.0102.json")
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
        ids = Survey.identifiers(reply, batchNr=3866)
        rv = CSFormatter.pck_lines(reply["data"], **ids._asdict())
        self.assertEqual([
            "FBFV003866{0}".format(datetime.date.today().strftime("%d/%m/%y")),
            "FV",
            "0004:49900001225C:200911",
            "0001 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], rv)


class PackingTests(unittest.TestCase):

    def test_tempdir(self):
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
            "data": {}
        }
        tfr = MWSSTransformer(response)
        self.assertEqual(
            "REC1204_0000.DAT",
            MWSSTransformer.idbr_name(
                **tfr.ids._asdict()
            )
        )
        try:
            tfr.pack(imgSeq=itertools.count())
        except KeyError:
            self.fail("TODO: define pages of survey.")
