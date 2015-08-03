# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.
"""
Tests for mixbox.signals.
"""

import unittest

from mixbox import signals

FOO_EMIT_VAL = 0xf00
FOO_SIGNAL = "foo.called"


class MockSender(object):
    def send(self, value=None):
        if not value:
            value = FOO_EMIT_VAL
        signals.emit(FOO_SIGNAL, value)


class MockReceiver(object):
    static_value = None
    class_value = None

    def __init__(self):
        self.value = None
        signals.connect(FOO_SIGNAL, self.receive)

    def receive(self, value):
        self.value = value

    def unbound(self):
        pass

    @staticmethod
    def static_receive(value):
        MockReceiver.static_value = value

    @classmethod
    def class_receive(cls, value):
        MockReceiver.class_value = value


class SignalsTests(unittest.TestCase):
    def test_func_receiver(self):
        """Test that signals are emitted and caught correctly."""
        class NonLocal:
            pass

        @signals.receiver(FOO_SIGNAL)
        def foo_handler(value):
            NonLocal.to_check = value

        m = MockSender()
        m.send()  # Should emit the signal and caught by foo_handler()

        self.assertEqual(NonLocal.to_check,FOO_EMIT_VAL)

    def test_bound_receiver(self):
        """Tests that mixbox signals correctly invoke bound method handlers."""
        receiver = MockReceiver()
        sender = MockSender()

        # Make sure that the receiver is initialized to None
        self.assertEqual(receiver.value, None)

        # Emit the signal
        sender.send()

        # Check that the receiver was updated correctly
        self.assertEqual(receiver.value, FOO_EMIT_VAL)

    def test_static_receiver(self):
        """Tests that a static method can be registerd as a receiver."""
        self.assertEqual(MockReceiver.static_value, None)

        signals.connect(FOO_SIGNAL, MockReceiver.static_receive)
        sender = MockSender()
        sender.send()
        self.assertEqual(MockReceiver.static_value, FOO_EMIT_VAL)

    def test_disconnect(self):
        """Tests that receiver disconnection returned True on success and False
        on failure (to map the receiver to the signal) and that the receiver
        is not called after disconnection.
        """
        sender = MockSender()
        receiver = MockReceiver()

        # Test that disconnecting a valid receiver returns True
        disconnected = signals.disconnect(FOO_SIGNAL, receiver.receive)
        self.assertTrue(disconnected)

        # Test that disconnecting an invalid receiver returns False
        disconnected = signals.disconnect(FOO_SIGNAL, receiver.static_receive)
        self.assertEqual(disconnected, False)

        # Test that the previously connected receiver is disconnected.
        expected = "THIS SHOULD NOT CHANGE"
        receiver.value = expected
        sender.send("IT CHANGED")
        self.assertEqual(expected, receiver.value)


if __name__ == "__main__":
    unittest.main()
