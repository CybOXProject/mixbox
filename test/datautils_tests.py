# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import unittest

from mixbox.datautils import is_sequence, needkwargs
from mixbox.vendor import six


class SequenceTests(unittest.TestCase):
    """Tests for the is_sequence function."""

    def test_string_type(self):
        # We are technically testing different things here in Python 2 and
        # Python 3, but in both cases a string (byte string or unicode string)
        # should not be a "sequence" by our definition.
        self.assertFalse(is_sequence(""))
        self.assertFalse(is_sequence(six.u("")))
        self.assertFalse(is_sequence(six.b("")))

    def test_dict_types(self):
        self.assertTrue(is_sequence(dict()))
        self.assertTrue(is_sequence({}))
        self.assertTrue(is_sequence({1: 2, 3: 4}))

    def test_list_types(self):
        self.assertTrue(is_sequence(list()))
        self.assertTrue(is_sequence([]))
        self.assertTrue(is_sequence([1, 2, 3, 4]))

    def test_set_types(self):
        self.assertTrue(is_sequence(set()))
        # Set literal syntax {1, 2, 3, 4} doesn't work on Python 2.6.
        self.assertTrue(is_sequence(set([1, 2, 3, 4])))

    def test_tuple_types(self):
        self.assertTrue(is_sequence(tuple()))
        self.assertTrue(is_sequence((1, 2, 3, 4)))


class NeedKwargTests(unittest.TestCase):
    """Tests for the needkwargs decorator."""

    def test_needkwargs(self):
        @needkwargs("foo", "bar")
        def foofunc(**kwargs):
            return True

        self.assertRaises(ValueError, foofunc)
        self.assertRaises(ValueError, foofunc, foo=1)
        self.assertRaises(ValueError, foofunc, bar=2)
        self.assertTrue(foofunc(foo=1, bar=2))
