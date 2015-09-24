# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.
"""
Utilities for dealing with XML namespaces.
"""

import collections

# A convenience class which represents simplified XML namespace info, consisting
# of exactly one namespace URI, and an optional prefix and schema location URI.
# This is handy for building up big tables of namespace data.
Namespace = collections.namedtuple("Namespace", "name prefix schema_location")

class DuplicatePrefixError(Exception):
    """Indicates an attempt to map a prefix to two different namespaces."""
    def __init__(self, prefix, *namespaces):
        super(DuplicatePrefixError, self).__init__(
            "Can't map prefix '{0}' to different namespaces: {1}".format(
                prefix, namespaces
            )
        )
        self.prefix = prefix
        self.namespaces = namespaces

class ConflictingSchemaLocationError(Exception):
    """Indicates an attempt to associated an XML namespace URI with two
    different schema location URIs."""
    def __init__(self, ns_uri, *schemalocs):
        super(ConflictingSchemaLocationError, self).__init__(
            "Can't map namespace '{0}' to different schema locations: {1}".format(
                ns_uri, schemalocs
            )
        )
        self.ns_uri = ns_uri
        self.schemalocs = schemalocs

class NamespaceNotFoundError(Exception):
    """Thrown when a namespace is not found.  The URI identifying the namespace
    is available from the "ns_uri" attribute."""
    def __init__(self, ns_uri):
        super(NamespaceNotFoundError, self).__init__(
            "Namespace not found: {0}".format(ns_uri)
        )
        self.ns_uri = ns_uri

class PrefixNotFoundError(Exception):
    """Thrown when a namespace prefix is not found.  The prefix is available
    from the "prefix" attribute."""
    def __init__(self, prefix):
        super(PrefixNotFoundError, self).__init__(
            "Prefix not found: {0}".format(prefix)
        )
        self.prefix = prefix

class TooManyDefaultNamespacesError(Exception):
    """Raised when creating xmlns attributes.  You can't have more than one
    default namespace in an XML document.  If a second preferred default is
    encountered, an attempt is made to choose a prefix from the set of
    registered prefixes.  If none are registered, this exception is raised."""
    def __init__(self, ns_uri):
        super(TooManyDefaultNamespacesError, self).__init__(
            "Too many default namespaces: needed a prefix for namespace '{0}' "
            "but none are defined!".format(ns_uri)
        )

class NoPrefixesError(Exception):
    """Thrown when prefixes are required for a namespace, but none are
    registered."""
    def __init__(self, ns_uri):
        super(NoPrefixesError, self).__init__(
            "Namespace '{0}' has no prefixes!",format(ns_uri)
        )

class NamespaceSet:
    """Represents a set of XML namespaces.  For each namespace, a set
    of prefixes and a schema location URI are also maintained.  Prefixes and
    schema location are optional; the namespace URI is always required.

    Each namespace has a preferred prefix.  If None, this indicates a
    preference that it be used as a default namespace.  At present, there is
    nothing preventing multiple namespaces from preferring to be default.  Of
    course, in any given XML document, there can only be one default.  The
    get_xmlns_string() function may throw if there are too many preferred
    default namespaces in this set."""

    class __NamespaceInfo:
        """Holds all info about a single XML namespace, including its URI, a
        set of prefixes, and a schema location URI.

        This is an internal class.  Some invariants must be maintained:
        preferred_prefix is a member of prefixes, or is None (meaning the
        preferred thing to do is use it as an XML default namespace).
        There must be no more than one instance per namespace URI.
        """

        def __init__(self, *args):
            """One arg is passed; it is expected to be a Namespace object, and
            this object is constructed from the given namespace.  This
            Namespace's prefix becomes the preferred prefix."""
            if len(args) == 0:
                # internal undocumented usage: normal users, don't do this!
                self.__default_construct()
            else:
                ns = args[0]
                self.__construct_from_namespace(ns)

        def __default_construct(self):
            """Default-construct this object.
            Internal use only; it constructs an invalid object.  Further
            initialization is required to make it valid.
            """
            self.uri = None
            self.schema_location = None
            self.prefixes = set()
            self.preferred_prefix = None

        def __construct_from_namespace(self, ns):
            """Initialize this instance from a given Namespace object."""
            assert isinstance(ns, Namespace)
            assert ns.name is not None # other fields are optional

            self.uri = ns.name
            self.schema_location = ns.schema_location or None
            self.prefixes = set()
            if ns.prefix:
                self.prefixes.add(ns.prefix)
            self.preferred_prefix = ns.prefix or None

        @classmethod
        def clone(cls, to_clone):
            assert isinstance(to_clone, cls)

            # the real reason for our undocumented default-construction!
            cloned_ni = cls()

            cloned_ni.uri = to_clone.uri
            cloned_ni.schema_location = to_clone.schema_location
            cloned_ni.prefixes = to_clone.prefixes.copy()
            cloned_ni.preferred_prefix = to_clone.preferred_prefix

            return cloned_ni

        def __str__(self):
            "for debugging"
            if self.preferred_prefix:
                preferred_prefix = self.preferred_prefix
            else:
                preferred_prefix = "(default)"
            return "\n  ".join((self.uri, str(self.prefixes),
                                "preferred: " + preferred_prefix,
                                str(self.schema_location)))

    def __init__(self):
        # Each mapped-to value in this map must be unique (a __NamespaceInfo).
        self.__ns_uri_map = {}
        # Mapped-to values in this map must refer to a mapped-to value in
        # __ns_uri_map.  More than one key may map to the same value.
        self.__prefix_map = {}

    def __add_namespaceinfo(self, ni):
        """Internal method to directly add a __NamespaceInfo object to this
        set."""
        self.__ns_uri_map[ni.uri] = ni
        for prefix in ni.prefixes:
            self.__prefix_map[prefix] = ni

    def __check_prefix_conflict(self, existing_ni_or_ns_uri, incoming_prefix):
        """If existing_ni_or_ns_uri is a __NamespaceInfo object, then caller
        wants to map incoming_prefix to that namespace.  This function verifies
        that the prefix isn't already mapped to a different namespace URI.  If
        it is, an exception is raised.

        Otherwise, existing_ni_or_ns_uri is treated as a string namespace URI
        which must not already exist in this set.  Caller wants to map
        incoming_prefix to that URI.  If incoming_prefix maps to anything
        already, that represents a prefix conflict and an exception is raised.
        """
        if isinstance(existing_ni_or_ns_uri, NamespaceSet.__NamespaceInfo):
            existing_ni = existing_ni_or_ns_uri # makes following code clearer?

            prefix_check_ni = self.__prefix_map.get(incoming_prefix)
            if prefix_check_ni is not None and \
                            prefix_check_ni is not existing_ni:
                # A different obj implies a different namespace URI is
                # already assigned to the prefix.
                raise DuplicatePrefixError(incoming_prefix, prefix_check_ni.uri,
                                           existing_ni.uri)
        else:
            ns_uri = existing_ni_or_ns_uri # makes following code clearer?

            assert isinstance(ns_uri, str)
            assert not self.contains_namespace(ns_uri)

            prefix_check_ni = self.__prefix_map.get(incoming_prefix)
            if prefix_check_ni is not None:
                raise DuplicatePrefixError(incoming_prefix, prefix_check_ni.uri,
                                           ns_uri)

    def contains_namespace(self, ns_uri):
        """Determines whether the namespace identified by ns_uri is in this
        set."""
        return ns_uri in self.__ns_uri_map

    def namespace_for_prefix(self, prefix):
        ni = self.__prefix_map.get(prefix)
        if ni:
            return ni.uri
        return None

    def preferred_prefix_for_namespace(self, ns_uri):
        """Get the "preferred" prefix for the given namespace.  Returns None
        if the preference is to use as the default namespace, or if the given
        namespace URI doesn't exist in this set.  Use
        `contains_namespace()` to distinguish the two cases."""
        ni = self.__ns_uri_map.get(ns_uri)
        if ni:
            return ni.preferred_prefix
        return None

    def set_preferred_prefix_for_namespace(self, ns_uri, prefix,
                                           add_if_not_exist=False):
        """Sets the preferred prefix for ns_uri.  If add_if_not_exist is True,
        the prefix is added if it's not already registered.  Otherwise,
        setting an unknown prefix as preferred is an error.  The default
        is False.  Setting to None always works, and indicates a preference
        to use the namespace as a default.  The given namespace must already
        be in this set.

        :param str ns_uri: the namespace URI whose prefix is to be set
        :param str prefix: the preferred prefix to set
        :param bool add_if_not_exist: Whether to add the prefix if it is not
           already set as a prefix of `ns_uri`.
        """

        ni = self.__ns_uri_map.get(ns_uri)
        if not ni:
            raise NamespaceNotFoundError(ns_uri)

        if not prefix:
            ni.preferred_prefix = None
        else:
            if add_if_not_exist:
                self.__check_prefix_conflict(ni, prefix)
                ni.prefixes.add(prefix)
                self.__prefix_map[prefix] = ni
            else:
                if prefix not in ni.prefixes:
                    raise PrefixNotFoundError(prefix)

            ni.preferred_prefix = prefix

    def prefixes_for_namespace(self, ns_uri):
        ni = self.__ns_uri_map.get(ns_uri)
        if ni:
            # Return a copy so users can't mess with the internal set.
            return set(ni.prefixes)
        return None

    def __merge_schema_locations(self, ni, incoming_schemaloc):
        """Merge incoming_schemaloc into the given `__NamespaceInfo`, ni.  If we
        don't have one yet and the incoming value is non-None, update ours
        with theirs.  This modifies ni."""
        if ni.schema_location and incoming_schemaloc:
            if ni.schema_location != incoming_schemaloc:
                raise ConflictingSchemaLocationError(ni.uri,
                                                     ni.schema_location,
                                                     incoming_schemaloc)
        elif ni.schema_location is None:
                ni.schema_location = incoming_schemaloc or None

    def add_namespace(self, ns):
        """Add a namespace from a `Namespace` object."""
        assert isinstance(ns, Namespace)
        assert ns.name

        ni = self.__ns_uri_map.get(ns.name)
        if ni:
            # We have a __NamespaceInfo object for this URI already.  So this
            # is a merge operation.
            #
            # We modify a copy of the real __NamespaceInfo so that we are
            # exception-safe: if something goes wrong, we don't end up with a
            # half-changed NamespaceSet.
            new_ni = NamespaceSet.__NamespaceInfo.clone(ni)

            # Reconcile prefixes
            if ns.prefix:
                self.__check_prefix_conflict(ni, ns.prefix)
                new_ni.prefixes.add(ns.prefix)

            self.__merge_schema_locations(new_ni, ns.schema_location)

            # At this point, we have a legit new_ni object.  Now we update
            # the set, ensuring our invariants.  This should replace
            # all instances of the old ni in this set.
            for prefix in new_ni.prefixes:
                self.__prefix_map[prefix] = new_ni
            self.__ns_uri_map[new_ni.uri] = new_ni

        else:
            # A brand new namespace.  The incoming prefix should not exist at
            # all in the prefix map.
            if ns.prefix:
                self.__check_prefix_conflict(ns.name, ns.prefix)

            ni = NamespaceSet.__NamespaceInfo(ns)
            self.__ns_uri_map[ns.name] = ni
            if ns.prefix:
                self.__prefix_map[ns.prefix] = ni

    def remove_namespace(self, ns_uri):
        """Removes the indicated namespace from this set."""
        ni = self.__ns_uri_map.get(ns_uri)
        if ni is not None:
            del self.__ns_uri_map[ns_uri]
            for prefix in ni.prefixes:
                del self.__prefix_map[prefix]

    def add_prefix(self, ns_uri, prefix, set_as_preferred=False):
        """Adds prefix for the given namespace URI.  The namespace must already
        exist in this set.  If set_as_preferred is True, also set this
        namespace as the preferred one.  Default is False.

        :param str ns_uri: The namespace URI to add the prefix to
        :param str prefix: The prefix to add
        :param bool set_as_preferred: Whether to set the new prefix as preferred
        """
        ni = self.__ns_uri_map.get(ns_uri)
        if ni is None:
            raise NamespaceNotFoundError(ns_uri)

        self.__check_prefix_conflict(ni, prefix)
        ni.prefixes.add(prefix)
        self.__prefix_map[prefix] = ni
        if set_as_preferred:
            ni.preferred_prefix = prefix

    def remove_prefix(self, prefix):
        """Removes prefix from this set.  This is a no-op if the prefix
        doesn't exist in it."""
        ni = self.__prefix_map.get(prefix)
        if ni is not None:
            ni.prefixes.discard(prefix)
            del self.__prefix_map[prefix]
            if ni.preferred_prefix == prefix:
                # Choose some other prefix as the new preferred.
                if len(ni.prefixes) == 0:
                    ni.preferred_prefix = None
                else:
                    ni.preferred_prefix = next(iter(ni.prefixes))

    def get_xmlns_string(self, ns_uris = None, sort = False):
        """Generates XML namespace declarations for namespaces in this
        set.  It must be suitable for use in an actual XML document,
        so an exception is raised if this can't be done, e.g. if it would
        have more than one default namespace declaration.

        If ns_uris is non-None, it should be an iterable over namespace URIs.
        Only the given namespaces will occur in the returned string.  If None,
        all namespace are included.

        If sort is True, the string is constructed from URIs in sorted order."""

        if ns_uris is None:
            ns_uris = self.__ns_uri_map.keys()

        if sort:
            ns_uris = sorted(ns_uris)

        have_default = False
        xmlns_str = ""
        for ns_uri in ns_uris:
            ni = self.__ns_uri_map.get(ns_uri)
            if not ni:
                raise NamespaceNotFoundError(ns_uri)

            if ni.preferred_prefix:
                xmlns_str += 'xmlns:{0}="{1}"'.format(ni.preferred_prefix,
                                                      ni.uri)
            else:
                if have_default:
                    # Already have a default namespace; try to choose a prefix
                    # for this one from the set of registered prefixes.
                    if len(ni.prefixes) == 0:
                        raise TooManyDefaultNamespacesError(ni.uri)
                    else:
                        xmlns_str += 'xmlns:{0}="{1}"'.format(
                            next(iter(ni.prefixes)), ni.uri
                        )
                else:
                    xmlns_str += 'xmlns="{0}"'.format(ni.uri)

                have_default = True
            xmlns_str += "\n"

        return xmlns_str

    def get_schemaloc_string(self, ns_uris = None, sort = False):
        """Returns a schemalocation attribute, formatted as:
        'xsi:schemaLocation="..."'.  If no namespaces in this set have
        any schema locations defined, returns None."""

        if not ns_uris:
            ns_uris = self.__ns_uri_map.keys()

        if sort:
            ns_uris = sorted(ns_uris)

        first = True
        schemaloc_str = ""
        for ns_uri in ns_uris:
            ni = self.__ns_uri_map[ns_uri]
            if not ni.schema_location:
                continue
            if not first:
                schemaloc_str += "\n"
            schemaloc_str += "{0.uri} {0.schema_location}".format(ni)
            first = False

        if len(schemaloc_str) == 0:
            return None

        return 'xsi:schemaLocation="{0}"'.format(schemaloc_str)

    def get_uri_prefix_map(self):
        """Constructs and returns a map from namespace URI to prefix,
        representing all namespaces in this set.  The prefix chosen for each
        namespace is its preferred prefix if it's not None.  If the preferred
        prefix is None, one is chosen at random from the set of registered
        prefixes.  It the latter situation, if no prefixes are registered,
        an exception is raised."""
        the_map = {}
        for ni in self.__ns_uri_map:
            if ni.preferred_prefix:
                the_map[ni.uri] = ni.preferred_prefix
            else:
                # The reason I don't let any namespace map to None here is that
                # I don't think generateDS supports it.  It requires prefixes
                # for all namespaces.
                if len(ni.prefixes) == 0:
                    raise NoPrefixesError(ni.uri)
                else:
                    the_map[ni.uri] = next(iter(ni.prefixes))

        return the_map

    @property
    def namespace_uris(self):
        """A generator over the namespace URIs stored in this set."""
        for uri in self.__ns_uri_map.keys():
            yield uri

    def subset(self, ns_uris):
        """Return a subset of this NamespaceSet containing only data for the
        given namespaces.  An exception is raised if any URIs in ns_uris
        are not found in this set."""
        sub_ns = NamespaceSet()
        for ns_uri in ns_uris:
            ni = self.__ns_uri_map.get(ns_uri)
            if ni is None:
                raise NamespaceNotFoundError(ns_uri)

            new_ni = NamespaceSet.__NamespaceInfo.clone(ni)

            # We should be able to reach into details of our own
            # implementation on another obj, right??  This makes the subset
            # operation faster.  We can set up the innards directly from a
            # cloned __NamespaceInfo.
            sub_ns._NamespaceSet__add_namespaceinfo(new_ni)

        return sub_ns

    def is_valid(self):
        "For debugging; does some sanity checks on this set."
        for ns_uri, ni in self.__ns_uri_map.items():
            if not ni.uri:
                return False, "uri not set in namespaceinfo"
            if ni.preferred_prefix is not None and \
               ni.preferred_prefix not in ni.prefixes:
                return False, "preferred prefix not in prefixes"
            for prefix in ni.prefixes:
                if not prefix:
                    return False, "empty value in prefix set"
                if prefix not in self.__prefix_map:
                    return False, "prefix not in prefix map"
                if self.__prefix_map[prefix] is not ni:
                    return False, "prefix map maps to wrong namespaceinfo"

        return True, "Ok"

    def __len__(self):
        """Return the number of namespaces in this set."""
        return len(self.__ns_uri_map)

    def __str__(self):
        "for debugging"
        return "\n\n".join(str(v) for v in self.__ns_uri_map.values())


__ALL_NAMESPACES = NamespaceSet()


def register_namespace(namespace):
    """Register a new Namespace with the global NamespaceSet."""

    __ALL_NAMESPACES.add_namespace(namespace)

def lookup_name(name):
    return __ALL_NAMESPACES.preferred_prefix_for_namespace(name)

def lookup_prefix(prefix):
    return __ALL_NAMESPACES.namespace_for_prefix(prefix)

def make_namespace_subset_from_uris(ns_uris):
    """Creates a subset of the global NamespaceSet containing info only for
    the given namespaces."""
    return __ALL_NAMESPACES.subset(ns_uris)

# def get_full_ns_map():
#     """Return a name: prefix mapping for all registered Namespaces."""
#     return __ALL_NAMESPACES.ns_map
#
# def get_full_prefix_map():
#     """Return a prefix: name mapping for all registered Namespaces."""
#     return __ALL_NAMESPACES.prefix_map


# def get_full_schemaloc_map():
#     """Return a name: schemalocation mapping for all registered Namespaces."""
#     return __ALL_NAMESPACES.schemaloc_map


def get_xmlns_string(ns_uris = None, sort = False):
    """Build a string with 'xmlns' definitions for every namespace in ns_set.

    :param iterable ns_set: set of Namespace objects
    """
    return __ALL_NAMESPACES.get_xmlns_string(ns_uris, sort)


def get_schemaloc_string(ns_uris = None, sort = False):
    """Build a "schemaLocation" string for every namespace in ns_uris.

    Args:
        ns_uris (iterable): set of Namespace objects
    """
    return __ALL_NAMESPACES.get_schemaloc_string(ns_uris, sort)


NS_XLINK = Namespace('http://www.w3.org/1999/xlink', 'xlink', '')
NS_XML_DSIG = Namespace('http://www.w3.org/2000/09/xmldsig#', 'ds', '')
NS_XML_SCHEMA = Namespace('http://www.w3.org/2001/XMLSchema', 'xs', '')
NS_XML_SCHEMA_INSTANCE = Namespace('http://www.w3.org/2001/XMLSchema-instance', 'xsi', '')

XML_NAMESPACES = NamespaceSet()

# Magic to automatically register all Namespaces defined in this module.
for k, v in dict(globals()).items():
    if k.startswith('NS_'):
        register_namespace(v)
        XML_NAMESPACES.add_namespace(v)
