# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import unittest

from mixbox.typedlist import TypedList


class MockType(object):
    pass


class TestTypedList(unittest.TestCase):

    def test_append_good_type(self):
        tl = TypedList(type=MockType)
        tl.append(MockType())

        self.assertTrue(len(tl) == 1)
        self.assertTrue(isinstance(tl[0], MockType))


    def test_append_bad_type(self):
        tl = TypedList(type=MockType)
        self.assertRaises(TypeError, tl.append, False)


if __name__ == "__main__":
    unittest.main()
