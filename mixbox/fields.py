# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

"""
Entity field data descriptors (TypedFields) and associated classes.
"""

from .datautils import is_sequence


class TypedField(object):

    def __init__(self, name, type_=None,
                 key_name=None, comparable=True, multiple=False,
                 preset_hook=None, postset_hook=None):
        """
        Create a new field.

        Args:
            `name` (str): name of the field as contained in the binding class.
            `type_` (type): Required type for values assigned to this field. If
                `None`, no type checking is performed.
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

    def __get__(self, instance, owner):
        # If we are calling this on a class, we want the actual Field, not its
        # value
        if not instance:
            return self

        return instance._fields.get(self, [] if self.multiple else None)

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
        return self.attr_name

    @property
    def key_name(self):
        if self._key_name:
            return self._key_name
        else:
            return self.name.lower()

    @property
    def attr_name(self):
        """The name of this field as an attribute name.

        This is identical to the key_name, unless the key name conflicts with
        a builtin Python keyword, in which case a single underscore is
        appended.

        This should match the name given to the TypedField class variable (see
        examples below), but this is not enforced.

        Examples:
            data = cybox.TypedField("Data", String)
            from_ = cybox.TypedField("From", String)
        """

        attr = self.key_name
        # TODO: expand list with other Python keywords
        if attr in ('from', 'class', 'type', 'with', 'for', 'id', 'type',
                'range'):
            attr = attr + "_"
        return attr
