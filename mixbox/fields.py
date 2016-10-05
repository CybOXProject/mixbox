# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.
"""
Entity field data descriptors (TypedFields) and associated classes.
"""
import functools
import inspect

from .datautils import is_sequence, resolve_class
from .typedlist import TypedList
from .dates import parse_date, parse_datetime, serialize_date, serialize_datetime
from .xml import strip_cdata, cdata
from .vendor import six
from .compat import long


def unset(entity, *types):
    """Unset the TypedFields on the input `entity`.

    Args:
        entity: A mixbox.Entity object.
        *types: A variable-length list of TypedField subclasses. If not
            provided, defaults to TypedField.
    """
    if not types:
        types = (TypedField,)

    fields = list(entity._fields.keys())
    remove = (x for x in fields if isinstance(x, types))

    for field in remove:
        del entity._fields[field]


def _matches(field, params):
    """Return True if the input TypedField `field` contains instance attributes
    that match the input parameters.

    Args:
        field: A TypedField instance.
        params: A dictionary of TypedField instance attribute-to-value mappings.

    Returns:
        True if the input TypedField matches the input parameters.
    """
    fieldattrs = six.iteritems(params)
    return all(getattr(field, attr) == val for attr, val in fieldattrs)


def iterfields(klass):
    """Iterate over the input class members and yield its TypedFields.

    Args:
        klass: A class (usually an Entity subclass).

    Yields:
        (class attribute name, TypedField instance) tuples.
    """
    is_field = lambda x: isinstance(x, TypedField)

    for name, field in inspect.getmembers(klass, predicate=is_field):
        yield name, field


def find(entity, **kwargs):
    """Return all TypedFields found on the input `Entity` that were initialized
    with the input **kwargs.

    Example:
        >>> find(myentity, multiple=True, type_=Foo)

    Note:
        TypedFields.__init__() can accept a string or a class as a type_
        argument, but this method expects a class.

    Args:
        **kwargs: TypedField __init__ **kwargs to search on.

    Returns:
        A list of TypedFields with matching **kwarg values.
    """
    try:
        typedfields = entity.typed_fields()
    except AttributeError:
        typedfields = iterfields(entity.__class__)

    matching = [x for x in typedfields if _matches(x, kwargs)]
    return matching


class TypedField(object):

    def __init__(self, name, type_=None,
                 key_name=None, comparable=True, multiple=False,
                 preset_hook=None, postset_hook=None, factory=None,
                 listfunc=None):
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
            `listfunc` (callable): A datatype or a function that creates a
                mutable sequence type for multiple field internal storage.
                E.g., "list".
        """
        self.name = name
        self.comparable = comparable
        self.multiple = multiple
        self.preset_hook = preset_hook
        self.postset_hook = postset_hook

        # The type of the field. This is lazily set via the type_ property
        # at first access.
        self._unresolved_type = type_

        # The factory for the field. This controls which class will be used
        # for from_dict() and from_obj() calls for this field.
        # Lazily set via the factory property.
        self._unresolved_factory = factory

        # Dictionary key name for the field.
        if key_name:
            self._key_name = key_name
        else:
            self._key_name = name.lower()

        # List creation function for multiple fields.
        if listfunc:
            self._listfunc = listfunc
        elif type_:
            self._listfunc = functools.partial(TypedList, type=type_)
        else:
            self._listfunc = list

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
            return instance._fields.setdefault(self, self._listfunc())
        else:
            return None

    def _clean(self, value):
        """Validate and clean a candidate value for this field."""
        if value is None:
            return None
        elif self.type_ is None:
            return value
        elif self.check_type(value):
            return value
        elif self.is_type_castable:  # noqa
            return self.type_(value)

        error_fmt = "%s must be a %s, not a %s"
        error = error_fmt % (self.name, self.type_, type(value))
        raise TypeError(error)

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
                value = self._listfunc()
            elif not is_sequence(value):
                value = self._listfunc([self._clean(value)])
            else:
                value = self._listfunc(self._clean(x) for x in value if x is not None)
        else:
            value = self._clean(value)

        if self.preset_hook:
            self.preset_hook(instance, value)

        instance._fields[self] = value

        if self.postset_hook:
            self.postset_hook(instance, value)

    def __str__(self):
        return self.name

    def check_type(self, value):
        if not self.type_:
            return True
        elif hasattr(self.type_, "istypeof"):
            return self.type_.istypeof(value)
        else:
            return isinstance(value, self.type_)

    @property
    def key_name(self):
        return self._key_name

    @property
    def type_(self):
        try:
            return self._resolved_type
        except AttributeError:
            self._resolved_type = resolve_class(self._unresolved_type)
        return self._resolved_type

    @type_.setter
    def type_(self, value):
        self._resolved_type = value

    @property
    def factory(self):
        try:
            return self._resolved_factory
        except AttributeError:
            self._resolved_factory = resolve_class(self._unresolved_factory)
        return self._resolved_factory

    @factory.setter
    def factory(self, value):
        self._resolved_factory = value

    @property
    def transformer(self):
        """Return the class for this field that transforms non-Entity objects
        (e.g., dicts or binding objects) into Entity instances.

        Any non-None value returned from this method should implement a
        from_obj() and from_dict() method.

        Returns:
            None if no type_ or factory is defined by the field. Return a class
            with from_dict and from_obj methods otherwise.
        """
        if self.factory:
            return self.factory
        elif self.type_:
            return self.type_
        else:
            return None

    @property
    def is_type_castable(self):
        return getattr(self.type_, "_try_cast", False)

    def binding_value(self, value):
        return value

    def dict_value(self, value):
        return value

    def __copy__(self):
        """See __deepcopy__."""
        return self

    def __deepcopy__(self, memo):
        """Return itself (don't actually make a copy at all).

        TypedFields store themselves as a key in an Entity._fields dictionary
        and use themselves as a key for value retrieval.

        The deepcopy() function would normally descend into the _fields dictionary
        of an Entity and replace the keys with *copies* of the original
        TypedFields.

        As such, a TypedField would never find itself in a deepcopied Entity,
        because the _fields dictionary had its keys swapped out for copies
        of the original TypedField.

        We could control __deepcopy__ at the Entity level, but it's a fair
        amount more complicated and ultimately, we probably never want
        TypedFields to actually be copied since they are class-level
        property descriptors.
        """
        memo[id(self)] = self  # add self to the memo so this isn't called again.
        return self


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
        if value in (None, ""):
            return None
        elif isinstance(value, six.string_types):
            return int(value, 0)
        else:
            return int(value)


class LongField(TypedField):
    def _clean(self, value):
        if value in (None, ""):
            return None
        elif isinstance(value, six.string_types):
            return long(value, 0)
        else:
            return long(value)


class FloatField(TypedField):
    def _clean(self, value):
        if value in (None, ""):
            return None
        return float(value)


class DateTimeField(TypedField):
    def _clean(self, value):
        return parse_datetime(value)

    def dict_value(self, value):
        return serialize_datetime(value)

    def binding_value(self, value):
        return serialize_datetime(value)


class DateField(TypedField):
    def _clean(self, value):
        return parse_date(value)

    def dict_value(self, value):
        return serialize_date(value)

    def binding_value(self, value):
        return serialize_datetime(value)


class CDATAField(TypedField):
    def _clean(self, value):
        return strip_cdata(value)

    def binding_value(self, value):
        return cdata(value)


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
