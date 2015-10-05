# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.
"""
Entity field data descriptors (TypedFields) and associated classes.
"""

import types
import importlib

from .datautils import is_sequence
from .dates import parse_date, parse_datetime
from .xml import strip_cdata
from .vendor import six


def unset(entity, *types):
    """Unset the TypedFields on the input `entity`.

    Args:
        entity: A mixbox.Entity object.
        *types: A variable-length list of TypedField subclasses. If not
            provided, defaults to TypedField.
    """
    if not types:
        types = [TypedField]

    fields = entity._fields.keys()
    remove = (x for x in fields if isinstance(x, types))

    for field in remove:
        del entity._fields[field]


def _import_class(classpath):
    """Import the class referred to by the fully qualified class path.

    Args:
        classpath: A full "A.B.CLASSNAME" package path to a class definition.

    Returns:
        The class referred to by the classpath.

    Raises:
        ImportError
    """
    modname, classname = classpath.rsplit(".", 1)
    module = importlib.import_module(modname)
    klass  = vars(module)[classname]
    return klass


class TypedField(object):

    def __init__(self, name, type_=None,
                 key_name=None, comparable=True, multiple=False,
                 preset_hook=None, postset_hook=None):
        """
        Create a new field.

        Args:
            `name` (str): name of the field as contained in the binding class.
            `type_` (type/str): Required type for values assigned to this field.
                If`None`, no type checking is performed. String values are
                treated as fully qualified package paths to a class (e.g.,
                "A.B.C" would be the full path to the type "C".)
            `key_name` (str): name for field when represented as a dictionary.
                (Optional) If omitted, `name.lower()` will be used.
            `comparable` (boolean): whether this field should be considered
                when checking Entities for equality. Default is True. If False,
                this field is not considered.
            `multiple` (boolean): Whether multiple instances of this field can
                exist on the Entity.
            `preset_hook` (callable): called before assigning a value to this
                field, but after type checking is performed (if applicable).
                This should typically be used to perform additional validation
                checks on the value, perhaps based on current state of the
                instance. The callable should accept two arguments: (1) the
                instance object being modified, and (2)the value it is being
                set to.
            `postset_hook` (callable): similar to `preset_hook` (and takes the
                same arguments), but is called after setting the value. This
                can be used, for example, to modify other fields of the
                instance to maintain some type of invariant.
        """
        self.name = name
        self.type_ = type_
        self._key_name = key_name
        self.comparable = comparable
        self.multiple = multiple
        self.preset_hook = preset_hook
        self.postset_hook = postset_hook

    def __get__(self, instance, owner=None):
        """Return the TypedField value for the input `instance` and `owner`.

        If the TypedField is a "multiple" field and hasn't been set yet,
        set the field to an empty list and return it.

        Args:
            instance: An instance of the `owner` class that this TypedField
                belongs to..
            owner: The TypedField owner class.
        """
        if instance is None:
            return self
        elif self in instance._fields:
            return instance._fields[self]
        elif self.multiple:
            return instance._fields.setdefault(self, [])
        else:
            return None

    def _clean(self, value):
        """Validate and clean a candidate value for this field."""
        if value is None:
            return None
        elif self.type_ is None:
            return value
        elif self.type_.istypeof(value):
            return value
        elif self.type_._try_cast:  # noqa
            return self.type_(value)

        error_fmt = "%s must be a %s, not a %s"
        error = error_fmt % (self.name, self.type_, type(value))
        raise ValueError(error)

    def __set__(self, instance, value):
        """Sets the field value on `instance` for this TypedField.

        If the TypedField has a `type_` and `value` is not an instance of
        ``type_``, an attempt may be made to convert `value` into an instance
        of ``type_``.

        If the field is ``multiple``, an attempt is made to convert `value`
        into a list if it is not an iterable type.
        """
        if self.multiple:
            if value is None:
                value = []
            elif not is_sequence(value):
                value = [self._clean(value)]
            else:
                value = [self._clean(x) for x in value if x is not None]
        else:
            value = self._clean(value)

        if self.preset_hook:
            self.preset_hook(instance, value)

        instance._fields[self] = value

        if self.postset_hook:
            self.postset_hook(instance, value)

    def __str__(self):
        return self.name

    @property
    def key_name(self):
        if self._key_name:
            return self._key_name
        else:
            return self.name.lower()

    @property
    def type_(self):
        if self._type is None:
            return None
        elif isinstance(self._type, types.TypeType):
            return self._type
        elif isinstance(self._type, basestring):
            self._type = _import_class(self._type)
            return self._type
        else:
            error = "Unknown TypedField type: '%s' and value: '%s'"
            error = error % (type(self._type), self._type)
            raise TypeError(error)

    @type_.setter
    def type_(self, value):
        self._type = value


class BytesField(TypedField):
    def _clean(self, value):
        return six.binary_type(value)


class TextField(TypedField):
    def _clean(self, value):
        return six.text_type(value)


class BooleanField(TypedField):
    def _clean(self, value):
        return bool(value)


class IntegerField(TypedField):
    def _clean(self, value):
        if value is not None:
            return int(value)


class DateTimeField(TypedField):
    def _clean(self, value):
        return parse_datetime(value)


class DateField(TypedField):
    def _clean(self, value):
        return parse_date(value)


class CDATAField(TypedField):
    def _clean(self, value):
        return strip_cdata(value)


class IdField(TypedField):
    def __set__(self, instance, value):
        """Set the id field to `value`. If `value` is not None or an empty
        string, unset the idref fields on `instance`.
        """
        super(IdField, self).__set__(instance, value)

        if value:
            unset(instance, IdrefField)


class IdrefField(TypedField):
    def __set__(self, instance, value):
        """Set the idref field to `value`. If `value` is not None or an empty
        string, unset the id fields on `instance`.
        """
        super(IdrefField, self).__set__(instance, value)

        if value:
            unset(instance, IdField)
