from collections import OrderedDict
import datetime
import unittest

from transform.transformers.MWSSTransformer import CSFormatter

class BatchFileTests(unittest.TestCase):

    def test_batch_header(self):
        batchNo = 3866
        batchDate = datetime.date(2009, 12, 29)
        rv = CSFormatter.batch_header(batchNo, batchDate)
        self.assertEqual("FBFV00386629/12/09", rv)

    def test_form_header(self):
        formId = 4
        ruRef = 49900001225
        check = "C"
        period = "200911"
        rv = CSFormatter.form_header(formId, ruRef, check, period)
        self.assertEqual("0004:49900001225C:200911", rv)

    def test_pck_lines(self):
        batchNo = 3866
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
        rv = CSFormatter.pck_lines(batchNo, batchDate, formId, ruRef, check, period, data)
        self.assertEqual([
            "FBFV00386629/12/09",
            "FV",
            "0004:49900001225C:200911",
            "0001 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], rv)
