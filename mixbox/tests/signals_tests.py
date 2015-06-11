# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.
"""
Tests for mixbox.signals.
"""

import unittest

from mixbox import signals

FOO_EMIT_VAL = 0xf00
FOO_SIGNAL = "foo.called"


class Mock(object):
    def foo(self):
        signals.emit(FOO_SIGNAL, FOO_EMIT_VAL)
        return


class SignalsTests(unittest.TestCase):
    def test_emit(self):
        """Test that signals are emitted and caught correctly.

        """
        # A hack to make inner functions access outer variables
        class NonLocal:
            pass

        @signals.handler(FOO_SIGNAL)
        def foo_handler(value):
            NonLocal.to_check = value

        m = Mock()
        m.foo()  # Should emit the signal and caught by foo_handler()

        self.assertEqual(NonLocal.to_check,FOO_EMIT_VAL)

if __name__ == "__main__":
    unittest.main()
