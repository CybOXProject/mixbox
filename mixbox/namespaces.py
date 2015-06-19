# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.
"""
Utilities for dealing with XML namespaces.
"""

from collections import MutableSet, namedtuple


class Namespace(namedtuple("Namespace", 'name prefix schema_location')):
    """An XML Namespace

    This subclasses namedtuple so that we can easily do attribute lookup while
    remaining immutable once created.

    Args:
        name (str): typically a URI
        prefix (str): the prefix for this Namespace
        schema_location (str): path to schema defining this Namespace
            (optional, should be '' if there is no defined schema)
    """


class NamespaceSet(MutableSet):
    """
    Flexible container for multiple namespaces.

    One of these exists as a private module-level variable in the
    mixbox.namespaces module to record all known namespaces. Other
    NamespaceSets can be created as needed.

    It also provides a variety of dictionary-style lookups to find a Namespace
    object by any of its attributes.

    As a set, it will prevent accidentally adding the same Namespace object
    multiple times, but will not prevent adding two Namespaces with the same
    name (URI).

    Note that the dictionary interfaces will only keep track of the most recent
    Namespace added with any particular name or prefix.

    TODO: We might want to add a feature that prevents adding two Namespaces
    with the same prefix but different URIs. But YAGNI, for now.
    """

    def __init__(self):
        self._inner = set()
        self.name_dict = {}
        self.prefix_dict = {}

    def __contains__(self, value):
        return self._inner.__contains__(value)

    def __iter__(self):
        return self._inner.__iter__()

    def __len__(self):
        return self._inner.__len__()

    def __repr__(self):
        return self._inner.__repr__()

    def add(self, value):
        assert isinstance(value, Namespace)
        self._inner.add(value)
        self.name_dict[value.name] = value
        self.prefix_dict[value.prefix] = value

    def discard(self, value):
        raise TypeError("NamespaceSet does not support removing Namespaces")


__ALL_NAMESPACES = NamespaceSet()


def register_namespace(namespace):
    """Register a new Namespace"""

    __ALL_NAMESPACES.add(namespace)


def lookup_name(name):
    return __ALL_NAMESPACES.name_dict[name]


def lookup_prefix(prefix):
    return __ALL_NAMESPACES.prefix_dict[prefix]


def get_xmlns_string(ns_set):
    """Build a string with 'xmlns' definitions for every namespace in ns_set.

    Args:
        ns_set (iterable): set of Namespace objects
    """
    xmlns_format = 'xmlns:{0.prefix}="{0.name}"'
    return "\n\t".join([xmlns_format.format(x) for x in ns_set])


def get_schemaloc_string(ns_set):
    """Build a "schemaLocation" string for every namespace in ns_set.

    Args:
        ns_set (iterable): set of Namespace objects
    """
    schemaloc_format = '{0.name} {0.schema_location}'
    # Only include schemas that have a schema_location defined (for instance,
    # 'xsi' does not.
    return " ".join([schemaloc_format.format(x) for x in ns_set
                     if x.schema_location])


NS_XLINK = Namespace('http://www.w3.org/1999/xlink', 'xlink', '')
NS_XML_DSIG = Namespace('http://www.w3.org/2000/09/xmldsig#', 'ds', '')
NS_XML_SCHEMA = Namespace('http://www.w3.org/2001/XMLSchema', 'xs', '')
NS_XML_SCHEMA_INSTANCE = Namespace('http://www.w3.org/2001/XMLSchema-instance', 'xsi', '')

# Magic to automatically register all Namespaces defined in this module.
for k, v in dict(globals()).items():
    if k.startswith('NS_'):
        register_namespace(v)
