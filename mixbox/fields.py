# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

"""
Entity field data descriptors (TypedFields) and associated classes.
"""

from .datautils import is_sequence


class TypedField(object):

    def __init__(self, name, type_=None, callback_hook=None, key_name=None,
                 comparable=True, multiple=False):
        """
        Create a new field.

        - `name` is the name of the field in the Binding class
        - `type_` is the type that objects assigned to this field must be.
          If `None`, no type checking is performed.
        - `key_name` is only needed if the desired key for the dictionary
          representation is differen than the lower-case version of `name`
        - `comparable` (boolean) - whether this field should be considered
          when checking Entities for equality. Default is True. If false, this
          field is not considered
        - `multiple` (boolean) - Whether multiple instances of this field can
          exist on the Entity.
        """
        self.name = name
        self.type_ = type_
        self.callback_hook = callback_hook
        self._key_name = key_name
        self.comparable = comparable
        self.multiple = multiple

    def __get__(self, instance, owner):
        # If we are calling this on a class, we want the actual Field, not its
        # value
        if not instance:
            return self

        return instance._fields.get(self.name, [] if self.multiple else None)

    def _handle_value(self, value):
        """Handles the processing of the __set__ value.

        """
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
                processed = []
            elif not is_sequence(value):
                processed = [self._handle_value(value)]
            else:
                processed = [self._handle_value(x) for x in value if x is not None]
        else:
            processed = self._handle_value(value)

        instance._fields[self.name] = processed

        if self.callback_hook:
            self.callback_hook(instance)

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
