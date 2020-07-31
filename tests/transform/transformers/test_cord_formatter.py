
import unittest

from transform.transformers.cord.cord_formatter import CORDFormatter


class CordFormatterTests(unittest.TestCase):

    def test_idbr_receipt(self):
        period = "1912"
        idbr = CORDFormatter.get_idbr("187", "12346789012", "A", period)
        self.assertEqual("12346789012:A:187:201912", idbr)

    def test_idbr_receipt_6_digit(self):
        period = "201912"
        idbr = CORDFormatter.get_idbr("187", "12346789012", "A", period)
        self.assertEqual("12346789012:A:187:201912", idbr)
