# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

# builtin
import unittest

# external
import dateutil.parser

# internal
from mixbox import dates
from mixbox.cache import IDTimestampCached, IDCached


ID_FOO = "example:foo"
ID_BAR = "example:bar"


class Foo(IDCached):
    def __init__(self):
        super(IDCached, self).__init__()
        self.id_ = None

    @property
    def id_(self):
        return self._id

    @id_.setter
    def id_(self, value):
        self._id = value


class Bar(IDTimestampCached):
    def __init__(self):
        super(IDTimestampCached, self).__init__()
        self.id_ = None
        self.timestamp = None

    @property
    def id_(self):
        return self._id

    @id_.setter
    def id_(self, value):
        self._id = value


class TestIDCacheable(unittest.TestCase):

    def test_cache_lookup(self):
        f = Foo()
        f.id_ = ID_FOO
        cached = Foo.cache_get(ID_FOO)
        self.assertTrue(f is cached)

    def test_cache_update(self):
        f = Foo()
        f.id_ = ID_FOO
        f.id_ = ID_BAR
        cached = Foo.cache_get(ID_BAR)
        self.assertTrue(f is cached)


    def test_cache_remove(self):
        f = Foo()
        f.id_ = ID_FOO
        f.id_ = ID_BAR

        # The ID
        self.assertEqual(Foo.cache_get(ID_FOO), None)

#
class TestIDTimestampCacheable(unittest.TestCase):

    def test_cache_lookup(self):
        b = Bar()
        b.id_ = ID_FOO
        b.timestamp = dates.now()

        cached = Bar.cache_get(id=b.id_, timestamp=b.timestamp)
        self.assertTrue(b is cached)

    def test_cache_update(self):
        b = Bar()
        b.id_ = ID_FOO
        b.id_ = ID_BAR
        cached = Bar.cache_get(ID_BAR, timestamp=None)
        self.assertTrue(b is cached)

    def test_cache_remove(self):
        b = Bar()

        b.timestamp = dates.now()
        b.id_ = ID_FOO
        b.id_ = ID_BAR

        cached = Bar.cache_get(id=ID_FOO, timestamp=b.timestamp)
        self.assertEqual(cached, None)

    def test_cache_ts_not_found(self):
        b = Bar()
        b.timestamp = dates.now()
        b.id_ = ID_BAR

        bad_date = dateutil.parser.parse("1970-01-01")
        cached = Bar.cache_get(id=ID_BAR, timestamp=bad_date)

        self.assertEqual(cached, None)

    def test_cache_lookup_all(self):
        coll = []

        for _ in xrange(10):
            b = Bar()
            b.id_= ID_FOO
            b.timestamp = dates.now()
            coll.append(b)

        all_cached = Bar.cache_get_all(ID_FOO)
        self.assertEqual(len(coll), len(all_cached))
