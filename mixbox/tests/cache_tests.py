# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

# builtin
import gc
import unittest

# external
from mixbox.vendor import six

# internal
from mixbox import dates, cache
from mixbox.cache import Cached, CacheMiss, MultipleCached

NOW = dates.now()

class Foo(Cached):
    def __init__(self, id_=None):
        super(Foo, self).__init__()
        self.id_ = id_
        self.timestamp = None

    @property
    def id_(self):
        return self._id

    @id_.setter
    def id_(self, value):
        self._id = value


class Bar(Cached):
    def __init__(self, id_=None):
        super(Bar, self).__init__()
        self.id_ = id_
        self.timestamp = None

    @property
    def id_(self):
        return self._id

    @id_.setter
    def id_(self, value):
        self._id = value



class TestCached(unittest.TestCase):

    def tearDown(self):
        gc.collect()

    def test_cache_lookup(self):
        f = Foo()
        f.id_ = "test_cache_lookup"
        cached = Foo.get("test_cache_lookup")
        self.assertTrue(f is cached)

    def test_cache_update(self):
        f = Foo()
        f.id_ = "foo"

        cached = Foo.get('foo')
        self.assertTrue(cached is f)

        f.id_ = "test_cache_update"

        cached = Foo.get("test_cache_update")
        self.assertTrue(f is cached)

        # Check that the old id was removed
        self.assertRaises(
            CacheMiss,
            Foo.get,
            'foo'
        )

    def test_cache_remove(self):
        f = Foo(id_='foo')
        f.id_ = "test_cache_remove"

        # The ID
        self.assertRaises(
            CacheMiss,
            Foo.get,
            "foo"
        )

    def test_id_timestamp_pair(self):
        f = Foo(id_='foo')
        f.timestamp = NOW

        cached = Foo.get('foo', timestamp=NOW)
        self.assertTrue(cached is f)

        self.assertRaises(
            CacheMiss,
            Foo.get,
            'bar',
            timestamp=NOW
        )

    def test_multiple(self):
        f1 = Foo()
        f2 = Foo()

        f1.id_ = f2.id_ = "foo"

        self.assertRaises(
            MultipleCached,
            Foo.get,
            'foo'
        )

    def test_count(self):
        l = [Foo(id_=x) for _ in six.moves.range(10) for x in six.moves.range(10)]
        self.assertEqual(cache.count(), len(l))

        # Now remove all strong references to Foo objects and recheck the count
        l = []
        gc.collect()
        self.assertEqual(cache.count(), 0)


if __name__ == "__main__":
    unittest.main()