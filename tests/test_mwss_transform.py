import datetime
import unittest

from transform.transformers.MWSSTransformer import CSFormatter

class BatchFileTests(unittest.TestCase):

    def test_header(self):
        batchNo = 3866
        batchDate = datetime.date(2009, 12, 29)
        rv = CSFormatter.header(batchNo, batchDate)
        self.assertEqual("FBFV00386629/12/09", rv)
