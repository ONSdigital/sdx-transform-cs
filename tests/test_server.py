import unittest

from server import bad_globals


class CheckGlobals(unittest.TestCase):

    def test_check_globals_negative(self):
        class MockModule:

            SDX_VAR1 = "some/path"
            SDX_VAR2 = None

        self.assertEqual(["SDX_VAR2"], bad_globals(MockModule))

    def test_check_globals_positive(self):
        class MockModule:

            SDX_VAR1 = "some/path"
            SDX_VAR2 = 8080

        self.assertEqual([], bad_globals(MockModule))
