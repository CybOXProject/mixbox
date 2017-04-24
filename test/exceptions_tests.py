# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import unittest

from mixbox.exceptions import ignored


def _divide_by_zero():
    return 1/0


class TestContextManagers(unittest.TestCase):

    def test_without_context_manager(self):
        self.assertRaises(ZeroDivisionError, _divide_by_zero)

    def test_with_context_manager(self):
        with ignored(ZeroDivisionError):
            _divide_by_zero()

            # This should never be reached, since the context manager should
            # exit after the error above.
            raise AssertionError()
