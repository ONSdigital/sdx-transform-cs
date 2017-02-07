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
