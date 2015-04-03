# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

# builtin
import collections

# Python 2.6 doesn't have WeakSet :(
try:
    from weakref import WeakSet
except ImportError:
    from weakrefset import WeakSet


class Cached(object):
    """Base mixin for managing object caches.

    This defines a class-level dictionary which maps class types to a set
    of object weakrefs.

    Note:
        Classes which utilize :class:`Cached` mixins will need to call
        super(Foo, self).__init__() to put itself in the cache.

    """
    _object_cache = collections.defaultdict(WeakSet)

    def __init__(self):
        object_cache = Cached._object_cache[self.__class__]
        object_cache.add(self)


class IDCached(Cached):
    """Mixin class which enables object caching and id-based lookups.

    """
    def __init__(self):
        super(IDCached, self).__init__()

    @classmethod
    def cache_get(cls, id):
        """Returns an object of type `cls` which has an ``id_`` property
        equal to `id`

        """
        # WeakSets can change during iteration if the garbage collector runs.
        # Make a local tuple to iterate over.
        object_cache = tuple(Cached._object_cache[cls])

        for cached in object_cache:
            if cached.id_ == id:
                return cached

        return None


class IDTimestampCached(Cached):
    """Mixin class which enables object caching and lookups via id and
    timestamp pairs.

    """
    def __init__(self):
        super(IDTimestampCached, self).__init__()

    @staticmethod
    def _matches(id, ts, item):
        """Returns ``True`` if the input `item` has an ``id_`` and
        ``timestamp`` which matches the input `id` and `ts` values.

        Note:
            Timestamps which contain UTC offset or tz information cannot
            be compared to timestamps that do not contain that information.
            Attempting to do so will raise a TypeError. If this occurs, we
            return ``False``.

        Args:
            id: An id to match against
            ts: A timestamp to match against
            item: An object with an ``id_`` and ``timestamp`` property.

        """
        try:
            return (item.id_ == id) and (item.timestamp == ts)
        except TypeError:
            return False

    @classmethod
    def cache_get(cls, id, timestamp=None):
        """Return a cached object with matching id and timestamp information.

        Args:
            id: The id of the cached item.
            timestamp: The timestamp of the cached item. Default is ``None``.

        """
        # WeakSets can change during iteration if the garbage collector runs.
        # Make a local tuple to iterate over.
        object_cache = tuple(Cached._object_cache[cls])

        for cached in object_cache:
            if cls._matches(id, timestamp, cached):
                return cached

        return None

    @classmethod
    def cache_get_all(cls, id):
        """Returns a tuple of cached objects that have matching id information.

        Args:
            id: The id of the cached item(s).

        """
        object_cache = tuple(Cached._object_cache[cls])
        return tuple(x for x in object_cache if x.id_ == id)
