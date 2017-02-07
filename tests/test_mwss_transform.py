from collections import OrderedDict
import datetime
import json
import unittest

from transform.transformers.MWSSTransformer import CSFormatter

import pkg_resources


class BatchFileTests(unittest.TestCase):

    def test_batch_header(self):
        batchNr = 3866
        batchDate = datetime.date(2009, 12, 29)
        rv = CSFormatter.batch_header(batchNr, batchDate)
        self.assertEqual("FBFV00386629/12/09", rv)

    def test_form_header(self):
        formId = 4
        ruRef = 49900001225
        check = "C"
        period = "200911"
        rv = CSFormatter.form_header(formId, ruRef, check, period)
        self.assertEqual("0004:49900001225C:200911", rv)

    def test_pck_lines(self):
        batchNr = 3866
        batchDate = datetime.date(2009, 12, 29)
        formId = 4
        ruRef = 49900001225
        check = "C"
        period = "200911"
        data = OrderedDict([
            ("0001", "{0:011}".format(2)),
            ("0140", "{0:011}".format(124)),
            ("0151", "{0:011}".format(217222))
        ])
        self.assertTrue(all(len(val) == 11 for val in data.values()))
        rv = CSFormatter.pck_lines(batchNr, batchDate, formId, ruRef, check, period, data)
        self.assertEqual([
            "FBFV00386629/12/09",
            "FV",
            "0004:49900001225C:200911",
            "0001 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], rv)

    def test_identifiers(self):
        reply = pkg_resources.resource_string(__name__, "pck/023.0102.json")
        data = json.loads(reply.decode("utf-8"))
        data["tx_id"] = "27923934-62de-475c-bc01-433c09fd38b8"
        ids = CSFormatter.identifiers(data)
        self.assertIsInstance(ids, CSFormatter.Identifiers)
        self.assertEqual(0, ids.batchNr)
        self.assertEqual(0, ids.seqNr)
        self.assertEqual(data["tx_id"], ids.txId)
        self.assertEqual(datetime.date.today(), ids.ts)
        self.assertEqual("023", ids.surveyId)
        self.assertEqual("RSI5B", ids.formId)
        self.assertEqual("12345678901", ids.ruRef)
        self.assertEqual("A", ids.ruChk)
        self.assertEqual("1604", ids.period)
