# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.
import collections
import sys

from .datautils import is_sequence, resolve_class, needkwargs
from .entities import EntityList
from .vendor import six


class TypedList(collections.MutableSequence):
    """A type-aware mutable sequence that performs input validation when
    inserting new items.

    Args:
        type: The type of the items contained in this collection.
        ignore_none: If True, do not insert None values.
        castfunc: A callable that will convert non-valid items into
            valid items.
        *args: A variable-length list of items to add to the collection.
            If an arg is a non-string, non-EntityList iterable type, each of
            its contained items will be added.
    """

    @needkwargs("type")
    def __init__(self, *args, **kwargs):
        self._inner       = []
        self._type        = resolve_class(kwargs["type"])
        self._castfunc    = kwargs.get("castfunc", self._type)
        self._ignore_none = kwargs.get("ignore_none", True)

        for item in args:
            if isinstance(item, EntityList):
                self.append(item)
            elif is_sequence(item):
                self.extend(item)
            else:
                self.append(item)

    def _is_valid(self, value):
        """Return True if the input value is valid for insertion into the
        inner list.

        Args:
            value: An object about to be inserted.
        """

        # Entities have an istypeof method that can perform more sophisticated
        # type checking.
        if hasattr(self._type, "istypeof"):
            return self._type.istypeof(value)
        else:
            return isinstance(value, self._type)

    def _fix_value(self, value):
        """Attempt to coerce value into the correct type.

        Subclasses can override this function.
        """
        try:
            return self._castfunc(value)
        except:
            error = "Can't put '{0}' ({1}) into a {2}. Expected a {3} object."
            error = error.format(
                value,                  # Input value
                type(value),            # Type of input value
                type(self),             # Type of collection
                self._type              # Expected type of input value
            )
            six.reraise(TypeError, TypeError(error), sys.exc_info()[-1])

    def _is_type_castable(self):
        return getattr(self._type, "_try_cast", False)

    def __nonzero__(self):
        return bool(self._inner)

    def __getitem__(self, key):
        return self._inner.__getitem__(key)

    def __setitem__(self, key, value):
        """Attempt to set the value at position `key` to the `value`.

        If a value is not the correct type, an attempt will be made to
        convert it to the correct type.

        Args:
            key: An index.
            value: A value to set.
        """
        if not self._is_valid(value):
            value = self._fix_value(value)
        self._inner.__setitem__(key, value)

    def __delitem__(self, key):
        self._inner.__delitem__(key)

    def __len__(self):
        return self._inner.__len__()

    def insert(self, idx, value):
        if value is None and self._ignore_none:
            return
        elif self._is_valid(value):
            self._inner.insert(idx, value)
        elif self._is_type_castable():
            value = self._fix_value(value)
            self._inner.insert(idx, value)
        else:
            err = "Cannot insert type (%s) into %s" % (type(value), type(self))
            raise TypeError(err)

    def __repr__(self):
        return self._inner.__repr__()

    def __str__(self):
        return self._inner.__str__()
