# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

# builtin
import collections

# internal
from mixbox.vendor import six

# Python 2.6 doesn't have WeakSet :(
try:
    from weakref import WeakSet
except ImportError:
    from weakrefset import WeakSet


# Internal object cache.
_CACHE = collections.defaultdict(WeakSet)

# Error messages
_CACHE_MISS_FMT = "No cached objects for id: '%s' and kwargs: %s"
_MULTIPLE_CACHED_FMT = "Multiple cached items for id: '%s' and kwargs: %s"


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
    """Mixin for managing object caches.

    """
    _cached_id_key = "id_"

    @classmethod
    def get(cls, id, **kwargs):
        """Proxy method to :meth:`mixbox.cache.get`.

        """
        return get(id, **kwargs)

    @classmethod
    def filter(cls, id, **kwargs):
        """Proxy method to :meth:`mixbox.cache.getall`.

        """
        return getall(id, **kwargs)


    def __setattr__(self, key, value):
        """Intercepts the object.__setattr__() and updates the mixbox
        object cache if the attr being set is equal to _cached_id_key.

        """
        # Get the previous value if it was set.
        prev = getattr(self, key, None)

        # Pass the call along
        super(Cached, self).__setattr__(key, value)

        # If the attribute being set is our cache id key, update the cache
        if key == self._cached_id_key:
            # Should I call `getattr(self, key)` here too in case the value was
            # mutated during super().__setattr__()?
            update(self, prev, value)


def _matches(obj, criteria):
    """Returns ``True`` if object contains attribute values that match the
    input `criteria`.

    Args:
        obj: A Python object.
        criteria: A tuple of attribute name/value pairs to compare object to.

    Raises:
        AttributeError if `obj` does not contain an attribute that is used
        in criteria.

    """
    try:
        return all(getattr(obj, k) == v for k, v in criteria)
    except (TypeError, ValueError):
        return False


def getall(key, **kwargs):
    """Returns a tuple of cached objects that have property values that match
    the input filter parameters.

    Example:
        >>> getall('example:Package-1')
        (obj1, obj2, obj3)
        >>> getall('example:Package-1', timestamp=some_timestamp)
        (obj1)
        >>> getall('example:Bad-ID')
        ()

    Args:
        key: An object identifier. Usually is usually an ``id_`` value.
        **kwargs: Other attribute name/value pairs to look for.

    """
    if key not in _CACHE:
        return ()

    # Need to convert the WeakSet to a tuple because the garbarge
    # collector could possibly modifiy the cache while we're iterating over
    # it.
    cached = tuple(_CACHE[key])

    if not kwargs:
        return cached

    # Shortening line length
    criteria = kwargs.items()

    # Find all cached objects which have attr values that align with
    # the input kwargs.
    filtered = tuple(x for x in cached if _matches(x, criteria))

    return filtered


def get(key, **kwargs):
    """Returns a single object that matches the input parameters.

    Args:
        key: An object key to look up.
        **kwargs: Other object-specific properties to use as filter criteria.

    Returns:
        A single Python object that matches the input criteria.

    Raises:
        CacheMiss: If no object exists for the given criteria.
        MultipleCached: If more than one object exists for the given critera.

    """
    cached = getall(key, **kwargs)

    if len(cached) == 1:
        return cached[0]

    if not cached:
        error = _CACHE_MISS_FMT % (key, kwargs)
        raise CacheMiss(error)

    error = _MULTIPLE_CACHED_FMT % (key, kwargs)
    raise MultipleCached(error)


def remove(key, item):
    """Removes the `item` from the cache.

    Args:
        item: The item to remove from the cache.
        key: The key for the cached item.

    """
    if key not in _CACHE:
        return

    # Remove self to the old ID group
    cached = _CACHE[key]
    cached.discard(item)

    if not cached:
        del _CACHE[key]


def add(key, item):
    """Adds the `item` to the cache.

    Args:
        item: The item to insert into the cache.
        key: The key for the cached item (an id).

    """
    _CACHE[key].add(item)


def update(item, old, new):
    """Updates the mixbox object cache. This will remove `obj` from the
    its old ID group in the cache and insert it into the new ID group.

    Args:
        item: The cached item.
        old: The old cache key for the item.
        new: The new cache key for the item.

    """
    # Remove the old entry
    remove(old, item)

    # Add the new entry
    add(new, item)


def count():
    """Returns the number of objects currently in the mixbox cache.

    """
    return sum(len(objlist) for objlist in six.itervalues(_CACHE))
