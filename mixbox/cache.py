# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

# builtin
import collections

# external
from mixbox.vendor import six

# Python 2.6 doesn't have WeakSet :(
try:
    from weakref import WeakSet
except ImportError:
    from weakrefset import WeakSet


_CACHE_MISS_FMT = "No cached %s for id '%s' and filter kwargs: %s"
_MULTIPLE_CACHED_FMT = ("Multiple cached %s for id '%s' and filter kwargs: "
                        "%s")


class MultipleCached(Exception):
    """Raised when multiple items are found in the cache for a
    given set of lookup parameters.

    """
    pass


class CacheMiss(Exception):
    """Raised when no items belong in the cache that match the criteria.

    """
    pass



class Cached(object):
    """Base mixin for managing object caches.

    This defines a class-level dictionary which maps class types to a set
    of object weakrefs.

    Note:
        Classes which utilize :class:`Cached` mixins will need to call
        super(Foo, self).__init__() to put itself in the cache.

    """
    _object_cache = collections.defaultdict(WeakSet)
    _id_key = "id_"

    def __init__(self):
        super(Cached, self).__init__()
        cache = Cached._object_cache[self.__class__]
        cache.add(self)

    @classmethod
    def _get_cached_instances(cls):
        object_cache = Cached._object_cache

        # Find all subclasses of cls that are in the object cache
        subclasses = (x for x in object_cache if issubclass(x, cls))

        # WeakSets can change during iteration if the garbage collector runs.
        # Coerce them into strong references by inserting objects into a list
        cached = []
        for subclass in subclasses:
            cache = tuple(object_cache.get(subclass, ()))
            cached.extend(cache)

        return cached

    @classmethod
    def filter(cls, id, **kwargs):
        # Get all cached instances of `cls`
        cached = cls._get_cached_instances()

        # Make sure that id is one of the filter criteria
        kwargs[cls._id_key] = id

        # Shortening line length
        kwargs = six.iteritems(kwargs)

        # Find all cached objects which have attr values that align with
        # the input kwargs.
        match = (x for x in cached if all(getattr(x, k) == v for k, v in kwargs))

        return tuple(match)

    @classmethod
    def get(cls, id, **kwargs):
        cached = cls.filter(id, **kwargs)

        if len(cached) == 1:
            return cached[0]

        if not cached:
            error = _CACHE_MISS_FMT % (cls.__name__, id, kwargs)
            raise CacheMiss(error)

        error = _MULTIPLE_CACHED_FMT % (cls.__name__, id, kwargs)
        raise MultipleCached(error)


