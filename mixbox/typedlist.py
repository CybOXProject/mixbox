# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.
import collections
import sys

from .datautils import is_sequence, resolve_class
from .entities import EntityList
from .vendor import six


class TypedList(collections.MutableSequence):
    """A type-aware mutable sequence that performs input validation when
    inserting new items.

    Args:
        type: The type of the items contained in this collection.
        ignore_none: If True, do not insert None values.
        *args: A variable-length list of items to add to the collection.
            If an arg is a non-string, non-EntityList iterable type, each of
            its contained items will be added.
    """

    def __init__(self, type, ignore_none=True, *args):
        self._inner = []
        self._type  = resolve_class(type)
        self._ignore_none = ignore_none

        for item in args:
            if isinstance(item, EntityList):
                self.append(item)
            elif is_sequence(item):
                self.extend(item)
            else:
                self.append(item)

    def _is_valid(self, value):
        if hasattr(self._type, "istypeof"):
            return self._type.istypeof(value)
        else:
            return isinstance(value, self._type)

    def _fix_value(self, value):
        """Attempt to coerce value into the correct type.

        Subclasses can override this function.
        """
        try:
            new_value = self._type(value)
        except:
            error = "Can't put '{0}' ({1}) into a {2}. Expected a {3} object."
            error = error.format(
                value,                  # Input value
                type(value),            # Type of input value
                type(self),             # Type of collection
                self._type              # Expected type of input value
            )
            six.reraise(TypeError, TypeError(error), sys.exc_info()[-1])

        return new_value

    def __nonzero__(self):
        return bool(self._inner)

    def __getitem__(self, key):
        return self._inner.__getitem__(key)

    def __setitem__(self, key, value):
        if not self._is_valid(value):
            value = self._fix_value(value)
        self._inner.__setitem__(key, value)

    def __delitem__(self, key):
        self._inner.__delitem__(key)

    def __len__(self):
        return len(self._inner)

    def insert(self, idx, value):
        if value is None and self._ignore_none:
            return
        elif not self._is_valid(value):
            value = self._fix_value(value)
        self._inner.insert(idx, value)

    def __repr__(self):
        return self._inner.__repr__()

    def __str__(self):
        return self._inner.__str__()
