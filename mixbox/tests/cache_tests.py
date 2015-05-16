# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

# builtin
import gc
import unittest

# external
import dateutil.parser

# internal
from mixbox import dates
from mixbox.cache import Cached, CacheMiss, MultipleCached


NOW = dates.now()


class Foo(Cached):
    def __init__(self):
        super(Foo, self).__init__()
        self.id_ = None
        self.timestamp = None

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
        f.id_ = "test_cache_update"

        cached = Foo.get("test_cache_update")
        self.assertTrue(f is cached)


    def test_cache_remove(self):
        f = Foo()
        f.id_ = "foo"
        f.id_ = "test_cache_remove"

        # The ID
        self.assertRaises(
            CacheMiss,
            Foo.get,
            "foo"
        )

    def test_id_timestamp_pair(self):
        f = Foo()
        f.id_ = 'foo'
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


if __name__ == "__main__":
    unittest.main()