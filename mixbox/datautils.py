# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

"""
Common routines for working with Python objects.
"""
import importlib

from .vendor import six


def is_sequence(value):
    """Determine if a value is a sequence type.

    Returns:
      ``True`` if `value` is a sequence type (e.g., ``list``, or ``tuple``).
      String types will return ``False``.

    NOTE: On Python 3, strings have the __iter__ defined, so a simple hasattr
    check is insufficient.
    """
    return (hasattr(value, "__iter__") and not
            isinstance(value, (six.string_types, six.binary_type)))


def import_class(classpath):
    """Import the class referred to by the fully qualified class path.

    Args:
        classpath: A full "foo.bar.MyClass" path to a class definition.

    Returns:
        The class referred to by the classpath.

    Raises:
        ImportError: If an error occurs while importing the module.
        AttributeError: IF the class does not exist in the imported module.
    """
    modname, classname = classpath.rsplit(".", 1)
    module = importlib.import_module(modname)
    klass  = getattr(module, classname)
    return klass


def resolve_class(classref):
    """Attempt to return a Python class for the input class reference.

    If `classref` is a class or None, return it. If `classref` is a
    python classpath (e.g., "foo.bar.MyClass") import the class and return
    it.

    Args:
        classref: A fully-qualified Python path to class, or a Python class.

    Returns:
        A class.
    """
    if classref is None:
        return None
    elif isinstance(classref, six.class_types):
        return classref
    elif isinstance(classref, six.string_types):
        return import_class(classref)
    else:
        raise ValueError("Unable to resolve class for '%s'" % classref)


class classproperty(object):
    """A ``property`` descriptor that works on classes rather than
    instances.

    Source:
        http://stackoverflow.com/a/3203659
    """

    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


def needkwargs(*argnames):
    """Function decorator which checks that the decorated function is called
    with a set of required kwargs.

    Args:
        *argnames: String keyword argument names.

    Raises:
        ValueError: If a required kwarg is missing in the decorated function
            call.
    """
    required = set(argnames)

    def decorator(func):
        def inner(*args, **kwargs):
            missing = required - set(kwargs)
            if missing:
                err = "%s kwargs are missing." % list(missing)
                raise ValueError(err)
            return func(*args, **kwargs)
        return inner
    return decorator
