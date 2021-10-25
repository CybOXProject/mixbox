# -*- coding: utf-8 -*-
# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

"""Tests for dates."""

import unittest
import datetime

from mixbox import dates


class DatesTests(unittest.TestCase):
    def test_parse_date(self):
        dstr = "2015-04-01"
        parsed = dates.parse_date(dstr)
        self.assertEqual(dstr, parsed.isoformat())
        
    def test_serialize_datetime_as_date(self):
        now = dates.now()
        self.assertTrue(isinstance(now, datetime.datetime))
        nowstr = dates.serialize_date(now)
        self.assertEqual(nowstr, now.date().isoformat())

    def test_parse_datetime(self):
        dtstr = '2015-04-02T16:44:30.423149+00:00'
        parsed = dates.parse_datetime(dtstr)
        self.assertEqual(dtstr, parsed.isoformat())

    def test_parse_datetime_none(self):
        parsed = dates.parse_datetime(None)
        self.assertEqual(parsed, None)

    def test_parse_date_none(self):
        parsed = dates.parse_date(None)
        self.assertEqual(parsed, None)

    def test_now(self):
        now = dates.now()
        self.assertTrue(isinstance(now, datetime.datetime))

    def test_serialize_date(self):
        now = dates.now().date()
        nowstr = now.isoformat()
        self.assertEqual(nowstr, dates.serialize_date(now))

    def test_serialize_datetime(self):
        now = dates.now()
        nowstr = now.isoformat()
        self.assertEqual(nowstr, dates.serialize_datetime(now))