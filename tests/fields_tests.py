# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import unittest

from mixbox.fields import TypedField


class TestTypedField(unittest.TestCase):

    def test_names(self):
        # The actual type is not important for this test
        a = TypedField("Some_Field", None)
        self.assertEqual("Some_Field", a.name)
        self.assertEqual("some_field", a.key_name)
        self.assertEqual("some_field", a.attr_name)

        a = TypedField("From", None)
        self.assertEqual("From", a.name)
        self.assertEqual("from", a.key_name)
        self.assertEqual("from_", a.attr_name)


if __name__ == "__main__":
    unittest.main()
