import unittest
from decimal import ROUND_HALF_UP

from transform.transformers.processor import Processor


class ProcessorTests(unittest.TestCase):

    def test_processor_unsigned(self):
        proc = Processor.unsigned_integer

        # Supply int default for range checking
        self.assertEqual(0, proc("q", {"q": -1.49}, 0))
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

    def test_processor_aggreggate(self):
        proc = Processor.aggregate

        # Supply int default for range checking
        self.assertEqual(0, proc("q", {"q": 0.49}, 0))
        self.assertEqual(101, proc("q", {"q": 101}, 0))
        self.assertEqual(0, proc("q", {"q": 0}, 0))

        proc = Processor.aggregate
        self.assertEqual(0, proc("q", {"q": 0.49}, 0, precision='1.',
                                 rounding_direction=ROUND_HALF_UP))
        self.assertEqual(101, proc("q", {"q": 100.5}, 0, precision='1.',
                                   rounding_direction=ROUND_HALF_UP))
        self.assertEqual(0, proc("q", {"q": 0}, 0, precision='1.',
                                 rounding_direction=ROUND_HALF_UP))

    def test_processor_boolean(self):
        proc = Processor.boolean

        # Supply int default for range checking
        self.assertEqual(True, proc("q", {"q": 0.49}, 0))
        self.assertEqual(True, proc("q", {"q": 101}, 0))
        self.assertEqual(False, proc("q", {"q": 0}, 0))
        self.assertEqual(False, proc("q", {"q": ""}, 0))

        proc = Processor.boolean
        self.assertEqual(True, proc("q", {"q": 0.49}, 0, precision='1.',
                                    rounding_direction=ROUND_HALF_UP))
        self.assertEqual(True, proc("q", {"q": 100.5}, 0, precision='1.',
                                    rounding_direction=ROUND_HALF_UP))
        self.assertEqual(False, proc("q", {"q": 0}, 0, precision='1.',
                                     rounding_direction=ROUND_HALF_UP)),
        self.assertEqual(False, proc("q", {"q": ""}, 0, precision='1.',
                                     rounding_direction=ROUND_HALF_UP))
