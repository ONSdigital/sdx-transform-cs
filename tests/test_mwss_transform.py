from collections import OrderedDict
import datetime
import json
import unittest

from transform.transformers.MWSSTransformer import CSFormatter
from transform.transformers.MWSSTransformer import MWSSTransformer
from transform.transformers.MWSSTransformer import Survey

import pkg_resources


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
        self.assertEqual(datetime.date.today(), ids.ts)
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


class TransformTests(unittest.TestCase):

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
        print(tfr.ops)

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
        }
        tfr = MWSSTransformer(response)
        self.assertEqual(
            "REC1204_0000.DAT",
            MWSSTransformer.idbr_name(
                response["submitted_at"],
                **tfr.ids._asdict()
            )
        )
        try:
            tfr.pack()
        except KeyError:
            self.fail("TODO: define pages.")
