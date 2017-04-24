# -*- coding: utf-8 -*-
# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

"""Tests for binding_utils"""

import unittest

from mixbox.vendor import six
from mixbox.vendor.six import u

from mixbox.binding_utils import quote_attrib, quote_xml

UNICODE_STR = u("❤ ♎ ☀ ★ ☂ ♞ ☯ ☭ ☢ €☎⚑ ❄♫✂")


class EncodingTests(unittest.TestCase):

    def test_quote_xml(self):
        s = quote_xml(UNICODE_STR)
        self.assertEqual(s, UNICODE_STR)

    def test_quote_attrib(self):
        """Tests that the quote_attrib method works properly on Unicode inputs.

        Note:
            The quote_attrib method (more specifically, saxutils.quoteattr())
            adds quotation marks around the input data, so we need to strip
            the leading and trailing chars to test effectively
        """
        s = quote_attrib(UNICODE_STR)
        s = s[1:-1]
        self.assertEqual(s, UNICODE_STR)

    def test_quote_attrib_int(self):
        i = 65536
        s = quote_attrib(i)
        self.assertEqual(u('"65536"'), s)

    def test_quote_attrib_bool(self):
        b = True
        s = quote_attrib(b)
        self.assertEqual(u('"True"'), s)

    def test_quote_xml_int(self):
        i = 65536
        s = quote_xml(i)
        self.assertEqual(six.text_type(i), s)

    def test_quote_xml_bool(self):
        b = True
        s = quote_xml(b)
        self.assertEqual(six.text_type(b), s)

    def test_quote_xml_zero(self):
        i = 0
        s = quote_xml(i)
        self.assertEqual(six.text_type(i), s)

    def test_quote_attrib_zero(self):
        i = 0
        s = quote_attrib(i)
        self.assertEqual(u('"0"'), s)

    def test_quote_xml_none(self):
        i = None
        s = quote_xml(i)
        self.assertEqual(u(''), s)

    def test_quote_attrib_none(self):
        i = None
        s = quote_attrib(i)
        self.assertEqual(u('""'), s)

    def test_quote_attrib_empty(self):
        i = ''
        s = quote_attrib(i)
        self.assertEqual(u('""'), s)

    def test_quote_xml_empty(self):
        i = ''
        s = quote_xml(i)
        self.assertEqual(u(''), s)

if __name__ == "__main__":
    unittest.main()
