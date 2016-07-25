# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.
"""
Utilities for dealing with XML namespaces.
"""

# stdlib
import collections
import copy

# external
from ordered_set import OrderedSet

# internal
from mixbox.vendor import six


_NamespaceTuple = collections.namedtuple("Namespace",
                                         "name prefix schema_location")

class Namespace(_NamespaceTuple):
    """A convenience class which represents simplified XML namespace info,
    consisting of exactly one namespace URI, and an optional prefix and schema
    location URI.  This is handy for building up big tables of namespace data.
    """
    def __new__(cls, name, prefix, schema_location=None):
        """This essentially enables parameter defaulting behavior on a
        namedtuple.  Here, schema location need not be given when creating a
        Namespace, and it will default to None."""
        return super(Namespace, cls).__new__(cls, name, prefix, schema_location)


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
            "Namespace '{0}' has no prefixes!".format(ns_uri)
        )


class InvalidNamespaceSetError(Exception):
    def __init__(self, msg):
        super(InvalidNamespaceSetError, self).__init__(
            "NamespaceSet is invalid: {0}".format(msg)
        )


class _NamespaceInfo(object):
    """**This class is an implementation detail of :class:`NamespaceSet`.
    Others must not use this class.**

    Holds all info about a single XML namespace, including its URI, a
    set of prefixes, and a schema location URI.

    This is an internal class.  Some invariants must be maintained:
    preferred_prefix is a member of prefixes, or is None (meaning the
    preferred thing to do is use it as an XML default namespace).
    There must be no more than one instance per namespace URI.  Other users
    may mess up the invariants, which is why this is "hidden".  The
    NamespaceSet public interface never uses this class.
    """

    def __init__(self, *args):
        """If a Namespace object is passed, this object is constructed from
        it.  If one to three strings are passed, they are treated as
        individual namespace components in the following order: URI, prefix,
        schema location.  Either way, the given prefix will become the
        preferred prefix.
        """
        iterargs = iter(args)
        ns       = next(iterargs, None)
        if ns is None:
            raise ValueError("At least one arg is required")

        if isinstance(ns, Namespace):
            self.__construct_from_namespace(ns)
        else:
            prefix    = next(iterargs, None)
            schemaloc = next(iterargs, None)
            self.__construct_from_components(ns, prefix, schemaloc)

    def __construct_from_namespace(self, ns):
        """Initialize this instance from a given Namespace object."""
        assert isinstance(ns, Namespace)  # TODO (bworrell): Change this to an if not isinstance(...): raise TypeError?
        self.__construct_from_components(*ns)

    def __construct_from_components(self, ns_uri, prefix=None, schema_location=None):
        """Initialize this instance from a namespace URI, and optional
        prefix and schema location URI."""

        assert ns_uri  # other fields are optional

        self.uri = ns_uri
        self.schema_location = schema_location or None
        self.prefixes = OrderedSet()

        if prefix:
            self.prefixes.add(prefix)
        self.preferred_prefix = prefix or None

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        return vars(other) == vars(self)

    def __ne__(self, other):
        """Python2 apparently needs this; python3 has a suitable default
        which delegates to __eq__.
        """
        return not self.__eq__(other)

    def __str__(self):
        """for debugging"""
        if self.preferred_prefix:
            preferred_prefix = self.preferred_prefix
        else:
            preferred_prefix = "(default)"

        s = "{0.uri}\n  {0.prefixes}\n  preferred: {1}\n  {0.schema_location}"
        return s.format(self, preferred_prefix)


class NamespaceSet(object):
    """Represents a set of XML namespaces.  For each namespace, a set
    of prefixes and a schema location URI are also maintained.  Prefixes and
    schema location are optional; the namespace URI is always required.

    Each namespace has a preferred prefix.  If None, this indicates a
    preference that it be used as a default namespace.  At present, there is
    nothing preventing multiple namespaces from preferring to be default.  Of
    course, in any given XML document, there can only be one default.  The
    get_xmlns_string() function may throw if there are too many preferred
    default namespaces in this set."""

    def __init__(self):
        # Each mapped-to value in this map must be unique (a _NamespaceInfo).
        self.__ns_uri_map = {}
        # Mapped-to values in this map must refer to a mapped-to value in
        # __ns_uri_map.  More than one key may map to the same value.
        self.__prefix_map = {}

    def __lookup_uri(self, uri):
        """Return a _NamespaceInfo object that is currently associated with the
        input namespace `uri`.
        """
        try:
            return self.__ns_uri_map[uri]
        except KeyError:
            raise NamespaceNotFoundError(uri)

    def __lookup_prefix(self, prefix):
        """Return a _NamespaceInfo object that is currently associated with the
        input `prefix`.
        """
        try:
            return self.__prefix_map[prefix]
        except KeyError:
            raise PrefixNotFoundError(prefix)

    def __add_namespaceinfo(self, ni):
        """Internal method to directly add a _NamespaceInfo object to this
        set.  No sanity checks are done (e.g. checking for prefix conflicts),
        so be sure to do it yourself before calling this."""
        self.__ns_uri_map[ni.uri] = ni
        for prefix in ni.prefixes:
            self.__prefix_map[prefix] = ni

    def __check_prefix_conflict(self, existing_ni_or_ns_uri, incoming_prefix):
        """If existing_ni_or_ns_uri is a _NamespaceInfo object (which must
        be in this set), then caller wants to map incoming_prefix to that
        namespace.  This function verifies that the prefix isn't already mapped
        to a different namespace URI.  If it is, an exception is raised.

        Otherwise, existing_ni_or_ns_uri is treated as a string namespace URI
        which must not already exist in this set.  Caller wants to map
        incoming_prefix to that URI.  If incoming_prefix maps to anything
        already, that represents a prefix conflict and an exception is raised.
        """
        if incoming_prefix not in self.__prefix_map:
            return

        # Prefix found in the prefix map. Check that there are no conflicts
        prefix_check_ni = self.__prefix_map[incoming_prefix]

        if isinstance(existing_ni_or_ns_uri, _NamespaceInfo):
            existing_ni = existing_ni_or_ns_uri  # makes following code clearer?

            if prefix_check_ni is not existing_ni:
                # A different obj implies a different namespace URI is
                # already assigned to the prefix.
                raise DuplicatePrefixError(incoming_prefix, prefix_check_ni.uri, existing_ni.uri)
        else:
            ns_uri = existing_ni_or_ns_uri  # makes following code clearer?
            assert not self.contains_namespace(ns_uri)  # TODO (bworrell): Should this be a raise?
            raise DuplicatePrefixError(incoming_prefix, prefix_check_ni.uri, ns_uri)

    def contains_namespace(self, ns_uri):
        """Determines whether the namespace identified by ns_uri is in this
        set.
        """
        return ns_uri in self.__ns_uri_map

    def __contains__(self, ns_uri):
        """Return True if the `ns_uri` is held by the NamespaceSet.  Just
        invokes contains_namespace().  This method enables the "X in Y" style
        of code to check for containment.

        Args:
            ns_uri: A namespace uri
        """
        return self.contains_namespace(ns_uri)

    def namespace_for_prefix(self, prefix):
        """Get the namespace the given prefix maps to.

        Args:
            prefix (str): The prefix

        Returns:
            str: The namespace, or None if the prefix isn't mapped to
                anything in this set.
        """
        try:
            ni = self.__lookup_prefix(prefix)
        except PrefixNotFoundError:
            return None
        else:
            return ni.uri

    def preferred_prefix_for_namespace(self, ns_uri):
        """Get the "preferred" prefix for the given namespace.  Returns None
        if the preference is to use as the default namespace."""
        ni = self.__lookup_uri(ns_uri)
        return ni.preferred_prefix

    def set_preferred_prefix_for_namespace(self, ns_uri, prefix, add_if_not_exist=False):
        """Sets the preferred prefix for ns_uri.  If add_if_not_exist is True,
        the prefix is added if it's not already registered.  Otherwise,
        setting an unknown prefix as preferred is an error.  The default
        is False.  Setting to None always works, and indicates a preference
        to use the namespace as a default.  The given namespace must already
        be in this set.

        Args:
            ns_uri (str): the namespace URI whose prefix is to be set
            prefix (str): the preferred prefix to set
            add_if_not_exist (bool): Whether to add the prefix if it is not
                already set as a prefix of ``ns_uri``.

        Raises:
            NamespaceNotFoundError: If namespace ``ns_uri`` isn't in this set.
            DuplicatePrefixError: If ``prefix`` already maps to a different
                namespace.
        """
        ni = self.__lookup_uri(ns_uri)

        if not prefix:
            ni.preferred_prefix = None
        elif prefix in ni.prefixes:
            ni.preferred_prefix = prefix
        elif add_if_not_exist:
            self.add_prefix(ns_uri, prefix, set_as_preferred=True)
        else:
            raise PrefixNotFoundError(prefix)

    def __merge_schema_locations(self, ni, incoming_schemaloc):
        """Merge incoming_schemaloc into the given `_NamespaceInfo`, ni.  If we
        don't have one yet and the incoming value is non-None, update ours
        with theirs.  This modifies ni.
        """
        if ni.schema_location == incoming_schemaloc:  # TODO (bworrell): empty strings?
            return
        elif not ni.schema_location:
            ni.schema_location = incoming_schemaloc or None
        elif not incoming_schemaloc:
            return
        else:
            raise ConflictingSchemaLocationError(ni.uri, ni.schema_location, incoming_schemaloc)

    def add_namespace(self, ns):
        """Add a namespace from a :class:`Namespace` object.  This method
        just passes off the tuple fields to :meth:`add_namespace_uri`."""
        assert isinstance(ns, Namespace)
        self.add_namespace_uri(*ns)

    def add_namespace_uri(self, ns_uri, prefix=None, schema_location=None):
        """Adds a new namespace to this set, optionally with a prefix and
        schema location URI.

        If the namespace already exists, the given prefix and schema location
        are merged with the existing entry:
            * If non-None, ``prefix`` is added to the set.  The preferred
                prefix is not modified.
            * If a schema location is not already associated with the
                namespace, it is set to ``schema_location`` (if given).

        If the namespace doesn't already exist in this set (so a new one is
        being created) and a prefix is given, that prefix becomes preferred.
        If not given, a preference as a default namespace is used.

        Args:
            ns_uri (str): The URI of the new namespace
            prefix (str): The desired prefix for the new namespace (optional)
            schema_location (str): The desired schema location for the new
                namespace (optional).

        Raises:
            DuplicatePrefixError: If a prefix is given which already maps to a
                different namespace
            ConflictingSchemaLocationError: If a schema location is given and
                the namespace already exists in this set with a different
                schema location.
        """
        assert ns_uri

        if ns_uri in self.__ns_uri_map:
            # We have a _NamespaceInfo object for this URI already.  So this
            # is a merge operation.
            #
            # We modify a copy of the real _NamespaceInfo so that we are
            # exception-safe: if something goes wrong, we don't end up with a
            # half-changed NamespaceSet.
            ni = self.__lookup_uri(ns_uri)
            new_ni = copy.deepcopy(ni)

            # Reconcile prefixes
            if prefix:
                self.__check_prefix_conflict(ni, prefix)
                new_ni.prefixes.add(prefix)

            self.__merge_schema_locations(new_ni, schema_location)

            # At this point, we have a legit new_ni object.  Now we update
            # the set, ensuring our invariants.  This should replace
            # all instances of the old ni in this set.
            for p in new_ni.prefixes:
                self.__prefix_map[p] = new_ni
            self.__ns_uri_map[new_ni.uri] = new_ni

        else:
            # A brand new namespace.  The incoming prefix should not exist at
            # all in the prefix map.
            if prefix:
                self.__check_prefix_conflict(ns_uri, prefix)

            ni = _NamespaceInfo(ns_uri, prefix, schema_location)
            self.__add_namespaceinfo(ni)

    def remove_namespace(self, ns_uri):
        """Removes the indicated namespace from this set."""
        if not self.contains_namespace(ns_uri):
            return

        ni = self.__ns_uri_map.pop(ns_uri)
        for prefix in ni.prefixes:
            del self.__prefix_map[prefix]

    def add_prefix(self, ns_uri, prefix, set_as_preferred=False):
        """Adds prefix for the given namespace URI.  The namespace must already
        exist in this set.  If set_as_preferred is True, also set this
        namespace as the preferred one.

        ``prefix`` must be non-None; a default preference can't be set this way.
        See :meth:`set_preferred_prefix_for_namespace` for that.

        Args:
            ns_uri (str): The namespace URI to add the prefix to
            prefix (str): The prefix to add (not None)
            set_as_preferred (bool): Whether to set the new prefix as preferred

        Raises:
            NamespaceNotFoundError: If namespace ``ns_uri`` isn't in this set
        """
        assert prefix

        ni = self.__lookup_uri(ns_uri)

        self.__check_prefix_conflict(ni, prefix)
        ni.prefixes.add(prefix)
        self.__prefix_map[prefix] = ni

        if set_as_preferred:
            ni.preferred_prefix = prefix

    def get_prefixes(self, ns_uri):
        """Gets (a copy of) the prefix set for the given namespace."""
        ni = self.__lookup_uri(ns_uri)
        return ni.prefixes.copy()

    def prefix_iter(self, ns_uri):
        """Gets an iterator over the prefixes for the given namespace."""
        ni = self.__lookup_uri(ns_uri)
        return iter(ni.prefixes)

    def remove_prefix(self, prefix):
        """Removes prefix from this set.  This is a no-op if the prefix
        doesn't exist in it.
        """
        if prefix not in self.__prefix_map:
            return

        ni = self.__lookup_prefix(prefix)
        ni.prefixes.discard(prefix)
        del self.__prefix_map[prefix]

        # If we removed the preferred prefix, find a new one.
        if ni.preferred_prefix == prefix:
            ni.preferred_prefix = next(iter(ni.prefixes), None)

    def get_schema_location(self, ns_uri):
        """Gets the schema location URI for the given namespace.

        Args:
            ns_uri (str): The namespace URI whose schema location is needed.

        Returns:
            The schema location, or None if none has been set.

        Raises:
            NamespaceNotFoundError: If the given namespace isn't in this set.
        """
        ni = self.__lookup_uri(ns_uri)
        return ni.schema_location

    def set_schema_location(self, ns_uri, schema_location, replace=False):
        """Sets the schema location of the given namespace.

        If ``replace`` is ``True``, then any existing schema location is
        replaced.  Otherwise, if the schema location is already set to a
        different value, an exception is raised.  If the schema location is set
        to None, it is effectively erased from this set (this is not considered
        "replacement".)

        Args:
            ns_uri (str): The namespace whose schema location is to be set
            schema_location (str): The schema location URI to set, or None
            replace (bool): Whether to replace any existing schema location

        Raises:
            NamespaceNotFoundError: If the given namespace isn't in this set.
            ConflictingSchemaLocationError: If replace is False,
                schema_location is not None, and the namespace already has a
                different schema location in this set.
        """
        ni = self.__lookup_uri(ns_uri)

        if ni.schema_location == schema_location:
            return
        elif replace or ni.schema_location is None:
            ni.schema_location = schema_location
        elif schema_location is None:
            ni.schema_location = None  # Not considered "replacement".
        else:
            raise ConflictingSchemaLocationError(ns_uri, ni.schema_location, schema_location)

    def get_xmlns_string(self, ns_uris=None, sort=False,
                         preferred_prefixes_only=True, delim="\n"):
        """Generates XML namespace declarations for namespaces in this
        set.  It must be suitable for use in an actual XML document,
        so an exception is raised if this can't be done, e.g. if it would
        have more than one default namespace declaration.

        If ``preferred_prefixes_only`` is ``True`` and a namespace's prefix
        preference is to be a default namespace, a default declaration will
        be used if possible.  If that's not possible, a prefix will be
        chosen (is this a good idea?).  If a default declaration can't be used
        and no other prefixes are defined, an exception is raised.

        Args:
            ns_uris (iterable): If non-None, it should be an iterable over
                namespace URIs.  Only the given namespaces will occur in the
                returned string.  If None, all namespace are included.
            sort (bool): If True, the string is constructed from URIs in sorted
                order.
            preferred_prefixes_only (bool): Whether to include only the
                preferred prefix or all of them, for each namespace.
            delim (str): The delimiter to use between namespace declarations.
                Should be some kind of whitespace.

        Returns:
            str: A string in the following format:
                ``xmlns:foo="bar"<delim>xmlns:foo2="bar2"<delim>...``

        Raises:
            NamespaceNotFoundError: If ``ns_uris`` is given and contains any
                URIs not in this set.
            TooManyDefaultNamespacesError: If too many namespaces didn't have
                a prefix.  The algorithm is very simple for deciding whose
                default preference is honored: the first default preference
                encountered gets to be default.  Any subsequent namespaces
                without any prefixes will cause this error.
        """
        if ns_uris is None:
            ns_uris = self.namespace_uris

        if sort:
            ns_uris = sorted(ns_uris)

        have_default  = False  # Flag for default xmlns entry.
        xmlns_entries = []     # Stores all the xmlns:prefix=uri entries.

        for ns_uri in ns_uris:
            ni = self.__lookup_uri(ns_uri)

            if preferred_prefixes_only:
                if ni.preferred_prefix is not None:
                    xmlns = 'xmlns:{0.preferred_prefix}="{0.uri}"'.format(ni)
                    xmlns_entries.append(xmlns)
            else:
                xmlns = 'xmlns:{0}="{1.uri}"'
                xmlns_entries.extend(xmlns.format(prefix, ni) for prefix in ni.prefixes)

            if ni.preferred_prefix is None:
                if have_default:
                    # Already have a default namespace; try to choose a prefix
                    # for this one from the set of registered prefixes.
                    if len(ni.prefixes) == 0:
                        raise TooManyDefaultNamespacesError(ni.uri)
                    elif preferred_prefixes_only:
                        prefix = next(iter(ni.prefixes))
                        xmlns  = 'xmlns:{0}="{1.uri}"'.format(prefix, ni)
                        xmlns_entries.append(xmlns)

                    # else, we already declared some prefixes for this
                    # namespace, so don't worry about our inability to use this
                    # as a default namespace.
                else:
                    xmlns = 'xmlns="{0.uri}"'.format(ni)
                    xmlns_entries.append(xmlns)
                    have_default = True

        xmlns_str = delim.join(xmlns_entries) + delim
        return xmlns_str

    def get_schemaloc_string(self, ns_uris=None, sort=False, delim="\n"):
        """Constructs and returns a schemalocation attribute.  If no
        namespaces in this set have any schema locations defined, returns
        an empty string.

        Args:
            ns_uris (iterable): The namespaces to include in the constructed
                attribute value.  If None, all are included.
            sort (bool): Whether the sort the namespace URIs.
            delim (str): The delimiter to use between namespace/schemaloc
                *pairs*.

        Returns:
            str: A schemalocation attribute in the format:
                ``xsi:schemaLocation="nsuri schemaloc<delim>nsuri2 schemaloc2<delim>..."``

        """
        if not ns_uris:
            ns_uris = six.iterkeys(self.__ns_uri_map)

        if sort:
            ns_uris = sorted(ns_uris)

        schemalocs = []

        for ns_uri in ns_uris:
            ni = self.__lookup_uri(ns_uri)

            if ni.schema_location:
                schemalocs.append("{0.uri} {0.schema_location}".format(ni))

        if not schemalocs:
            return ""

        return 'xsi:schemaLocation="{0}"'.format(delim.join(schemalocs))

    def get_uri_prefix_map(self):
        """Constructs and returns a map from namespace URI to prefix,
        representing all namespaces in this set.  The prefix chosen for each
        namespace is its preferred prefix if it's not None.  If the preferred
        prefix is None, one is chosen from the set of registered
        prefixes.  In the latter situation, if no prefixes are registered,
        an exception is raised.
        """
        mapping = {}
        
        for ni in six.itervalues(self.__ns_uri_map):
            if ni.preferred_prefix:
                mapping[ni.uri] = ni.preferred_prefix
            elif len(ni.prefixes) > 0:
                mapping[ni.uri] = next(iter(ni.prefixes))
            else:
                # The reason I don't let any namespace map to None here is that
                # I don't think generateDS supports it.  It requires prefixes
                # for all namespaces.
                raise NoPrefixesError(ni.uri)

        return mapping

    def get_prefix_uri_map(self):
        """Constructs and returns a map from to prefix to namespace URI,
        representing all namespaces in this set.  The prefix chosen for each
        namespace is its preferred prefix if it's not None.  If the preferred
        prefix is None, one is chosen from the set of registered
        prefixes.  In the latter situation, if no prefixes are registered,
        an exception is raised.
        """
        mapping = {}

        for ni in six.itervalues(self.__ns_uri_map):
            if ni.preferred_prefix:
                mapping[ni.preferred_prefix] = ni.uri
            elif len(ni.prefixes) > 0:
                prefix = next(iter(ni.prefixes))
                mapping[prefix] = ni.uri
            else:
                raise NoPrefixesError(ni.uri)

        return mapping

    def get_uri_schemaloc_map(self):
        """Constructs and returns a map from namespace URI to schema location
        URI.  Namespaces without schema locations are excluded."""
        mapping = {}

        for ni in six.itervalues(self.__ns_uri_map):
            if ni.schema_location:
                mapping[ni.uri] = ni.schema_location

        return mapping

    @property
    def namespace_uris(self):
        """A generator over the namespace URIs stored in this set."""
        for uri in six.iterkeys(self.__ns_uri_map):
            yield uri

    def subset(self, ns_uris):
        """Return a subset of this NamespaceSet containing only data for the
        given namespaces.

        Args:
            ns_uris (iterable): An iterable of namespace URIs which select the
                namespaces for the subset.

        Returns:
            The subset

        Raises:
            NamespaceNotFoundError: If any namespace URIs in `ns_uris` don't
                match any namespaces in this set.
        """
        sub_ns = NamespaceSet()

        for ns_uri in ns_uris:
            ni = self.__lookup_uri(ns_uri)
            new_ni = copy.deepcopy(ni)

            # We should be able to reach into details of our own
            # implementation on another obj, right??  This makes the subset
            # operation faster.  We can set up the innards directly from a
            # cloned _NamespaceInfo.
            sub_ns._NamespaceSet__add_namespaceinfo(new_ni)

        return sub_ns

    def import_from(self, other_ns, replace=False):
        """Imports namespaces into this set, from other_ns.

        Args:
            other_ns (NamespaceSet): The set to import from
            replace (bool): If a namespace exists in both sets, do we replace
                our data with other_ns's data?  We could get fancy and define
                some merge strategies, but for now, this is very simple.  It's
                either do nothing, or wholesale replacement.  There is no
                merging.

        Raises:
            DuplicatePrefixError: If the other NamespaceSet is mapping any
                prefixes incompatibly with respect to this set.
        """
        for other_ns_uri in other_ns.namespace_uris:
            ni = self.__ns_uri_map.get(other_ns_uri)

            if ni is None:
                other_ni = other_ns._NamespaceSet__ns_uri_map[other_ns_uri]

                # Gotta make sure that the other set isn't mapping its prefixes
                # incompatibly with respect to this set.
                for other_prefix in other_ni.prefixes:
                    self.__check_prefix_conflict(other_ns_uri, other_prefix)

                cloned_ni = copy.deepcopy(other_ni)
                self.__add_namespaceinfo(cloned_ni)
            elif replace:
                other_ni = other_ns._NamespaceSet__ns_uri_map[other_ns_uri]
                for other_prefix in other_ni.prefixes:
                    self.__check_prefix_conflict(ni, other_prefix)

                cloned_ni = copy.deepcopy(other_ni)
                self.remove_namespace(other_ns_uri)
                self.__add_namespaceinfo(cloned_ni)
            else:
                continue  # TODO (bworrell): Should this log/warn/do anything else?

    def assert_valid(self):
        """For debugging; does some sanity checks on this set.  Raises
        InvalidNamespaceSetError if this namespace set is invalid.  Otherwise,
        raises/returns nothing."""

        for ns_uri, ni in six.iteritems(self.__ns_uri_map):
            if not ni.uri:
                raise InvalidNamespaceSetError(
                    "URI not set in _NamespaceInfo (id={0}):\n{1}".format(
                        id(ni), ni
                    )
                )

            if ns_uri != ni.uri:
                raise InvalidNamespaceSetError(
                    "URI mismatch in dict ({0}) and _NamespaceInfo ({1})".format(
                        ns_uri, ni.uri
                    )
                )

            if (ni.preferred_prefix is not None and
               ni.preferred_prefix not in ni.prefixes):
                raise InvalidNamespaceSetError(
                    "Namespace {0.uri}: preferred prefix " \
                    '"{0.preferred_prefix}" not in prefixes ' \
                    "{0.prefixes}".format(ni)
                )

            for prefix in ni.prefixes:
                if not prefix:
                    raise InvalidNamespaceSetError(
                        "Namespace {0.uri}: empty value in prefix " \
                        "set: {0.prefixes}".format(ni)
                    )
                other_ni = self.__prefix_map.get(prefix)
                if other_ni is None:
                    raise InvalidNamespaceSetError(
                        'Namespace {0.uri}: prefix "{1}" not in ' \
                        'prefix map'.format(ni, prefix)
                    )
                if other_ni is not ni:
                    raise InvalidNamespaceSetError(
                        'Namespace {0.uri}: prefix "{1}" maps to ' \
                        'wrong _NamespaceInfo (id={2}, uri={3.uri})'.format(
                            ni, prefix, id(other_ni), other_ni
                        )
                    )

        if None in self.__prefix_map:
            # None can be a preferred prefix, but should not be in the
            # prefix map.
            raise InvalidNamespaceSetError("None is in prefix map!")

    def is_valid(self):
        """Does some sanity checks on this set.  Returns True if the set is
        valid, False otherwise."""
        try:
            self.assert_valid()
        except InvalidNamespaceSetError:
            return False

        return True

    def __len__(self):
        """Return the number of namespaces in this set."""
        return len(self.__ns_uri_map)

    def __eq__(self, other):
        """Test two namespaces for equality.  For them to be equal, they must
        contain the same namespaces, and for each namespace, their prefixes,
        schema location, and preferred prefix must also be the same."""

        if type(other) != type(self):
            return False
        elif len(other) != len(self):
            return False
        else:
            return self.__ns_uri_map == other._NamespaceSet__ns_uri_map

    def __ne__(self, other):
        """Python2 apparently needs this; python3 has a suitable default
        which delegates to __eq__.
        """
        return not self.__eq__(other)

    def __str__(self):
        """for debugging"""
        return "\n\n".join(str(v) for v in six.itervalues(self.__ns_uri_map))


__ALL_NAMESPACES = NamespaceSet()


def register_namespace(namespace):
    """Register a new Namespace with the global NamespaceSet."""

    __ALL_NAMESPACES.add_namespace(namespace)


def lookup_name(ns_uri):
    """Return the preferred prefix for the input namespace uri."""
    return __ALL_NAMESPACES.preferred_prefix_for_namespace(ns_uri)


def lookup_prefix(prefix):
    """Return the namespace uri that is mapped to the input prefix."""
    return __ALL_NAMESPACES.namespace_for_prefix(prefix)


def make_namespace_subset_from_uris(ns_uris):
    """Creates a subset of the global NamespaceSet containing info only for
    the given namespaces."""
    return __ALL_NAMESPACES.subset(ns_uris)


def get_full_ns_map():
    """Return a name: prefix mapping for all registered Namespaces."""
    return __ALL_NAMESPACES.get_uri_prefix_map()


def get_full_prefix_map():
    """Return a prefix: name mapping for all registered Namespaces."""
    return __ALL_NAMESPACES.get_prefix_uri_map()


def get_full_schemaloc_map():
    """Return a name: schemalocation mapping for all registered Namespaces."""
    return __ALL_NAMESPACES.get_uri_schemaloc_map()


def get_xmlns_string(ns_uris=None, sort=False):
    """Build a string with 'xmlns' definitions for every namespace in ns_uris.
    If ns_uris is None, all namespaces are included.

    Args:
        ns_uris (iterable): the namespace URIs, or None
    """
    return __ALL_NAMESPACES.get_xmlns_string(ns_uris, sort)


def get_schemaloc_string(ns_uris=None, sort=False):
    """Build a "schemaLocation" string for every namespace in ns_uris.
    If ns_uris is None, all namespaces are included.

    Args:
        ns_uris (iterable): the namespace URIs, or None
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
