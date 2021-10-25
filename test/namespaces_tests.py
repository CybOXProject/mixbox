# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import operator
import re
import unittest

import mixbox.namespaces
from mixbox.namespaces import Namespace, NamespaceSet


class TestNamespace(unittest.TestCase):

    def test_namedtuple(self):
        # Verify behavior of the namedtuple (mainly, that you can access
        # attributes but not modify them.
        ns = Namespace("http://example.com/", "example", "")
        self.assertEqual("http://example.com/", ns.name)
        self.assertEqual("example", ns.prefix)
        self.assertEqual("", ns.schema_location)

        self.assertRaises(AttributeError, setattr, ns, 'name', "urn:example")
        self.assertRaises(AttributeError, setattr, ns, 'prefix', "example")
        self.assertRaises(AttributeError, setattr, ns, 'schema_location', "")

    def test_equal(self):
        # Tuple equality is provided for free by namedtuple. Every element must
        # be equal for the Namespaces to be seen as equal
        ns1 = Namespace("http://example.com/", "example", "")
        ns2 = Namespace("http://example.com/", "example", "")
        ns3 = Namespace("http://example.com", "example", "")

        self.assertEqual(ns1, ns2)
        self.assertNotEqual(ns1, ns3)


class TestNamespaceSet(unittest.TestCase):

    def test_set_semantics(self):
        nsset = NamespaceSet()
        self.assertEqual(0, len(nsset))

        ns1 = Namespace("http://example.com/", "example", "")
        nsset.add_namespace(ns1)
        self.assertEqual(1, len(nsset))

        # Adding the same namespace doesn't have an effect
        nsset.add_namespace(ns1)
        self.assertEqual(1, len(nsset))

        # Neither does adding a new namespace object that is "equal" to the
        # first.
        nsset.add_namespace(Namespace("http://example.com/", "example", ""))
        self.assertEqual(1, len(nsset))

        # Adding a prefix doesn't change the set size
        nsset.add_namespace_uri("http://example.com/", "example2")
        self.assertEqual(1, len(nsset))

        self.assertTrue(nsset.contains_namespace("http://example.com/"))

        self.assertTrue(nsset.is_valid())

    def test_prefixes(self):
        ns = NamespaceSet()
        ns.add_namespace_uri("a:b:c", "pfx")
        ns.add_namespace_uri("a:b:c", "pfx2")
        ns.add_prefix("a:b:c","pfx3")
        self.assertEqual(len(ns.get_prefixes("a:b:c")), 3)
        self.assertTrue(ns.is_valid())

        ns.remove_prefix("pfx3")
        self.assertEqual(len(ns.get_prefixes("a:b:c")), 2)
        self.assertTrue(ns.is_valid())

        # Make sure prefix_iter() gives the same prefixes as get_prefixes().
        self.assertEqual(len(ns.get_prefixes("a:b:c")),
                         len(list(ns.prefix_iter("a:b:c"))))
        #self.assertTrue(all(map(operator.eq, ns.get_prefixes("a:b:c"),
        #                        ns.prefix_iter("a:b:c"))))
        # One time, I saw the above test code fail.  I never saw it again.
        # Seems like the prefixes may have come out in a different order or
        # something... guess I'll play it safe and copy them to sorted
        # lists before comparing.
        pfxs1 = sorted(ns.get_prefixes("a:b:c"))
        pfxs2 = sorted(ns.prefix_iter("a:b:c"))
        self.assertTrue(all(map(operator.eq, pfxs1, pfxs2)))

        self.assertEqual(ns.namespace_for_prefix("pfx"), "a:b:c")
        self.assertEqual(ns.namespace_for_prefix("pfx2"), "a:b:c")

        # Should get an exception if we try to map the same prefix to a
        # different namespace.
        self.assertRaises(mixbox.namespaces.DuplicatePrefixError,
                          ns.add_namespace_uri, "x:y:z", "pfx")
        self.assertRaises(mixbox.namespaces.DuplicatePrefixError,
                          ns.add_namespace, Namespace("x:y:z", "pfx", None))

        self.assertRaises(mixbox.namespaces.NamespaceNotFoundError,
                          ns.get_prefixes, "does:not:exist")
        self.assertRaises(mixbox.namespaces.NamespaceNotFoundError,
                          ns.prefix_iter, "does:not:exist")
        self.assertRaises(mixbox.namespaces.NamespaceNotFoundError,
                          ns.add_prefix, "does:not:exist", "dne")

        ns.remove_prefix("does:not:exist")

        self.assertTrue(ns.is_valid())

    def test_preferred_prefixes(self):
        ns = NamespaceSet()
        ns.add_namespace_uri("a:b:c", "abc")
        ns.add_namespace_uri("a:b:c", "def")
        self.assertEqual(ns.preferred_prefix_for_namespace("a:b:c"), "abc")

        ns.set_preferred_prefix_for_namespace("a:b:c", "def")
        self.assertEqual(ns.preferred_prefix_for_namespace("a:b:c"), "def")

        ns.set_preferred_prefix_for_namespace("a:b:c", None)

        ns.set_preferred_prefix_for_namespace("a:b:c", "ghi", True)
        self.assertEqual(ns.preferred_prefix_for_namespace("a:b:c"), "ghi")

        ns.add_prefix("a:b:c", "jkl", True)
        self.assertEqual(ns.preferred_prefix_for_namespace("a:b:c"), "jkl")

        self.assertRaises(mixbox.namespaces.NamespaceNotFoundError,
                          ns.preferred_prefix_for_namespace, "does:not:exist")
        self.assertRaises(mixbox.namespaces.NamespaceNotFoundError,
                          ns.set_preferred_prefix_for_namespace,
                          "does:not:exist", "dne")
        self.assertRaises(mixbox.namespaces.PrefixNotFoundError,
                          ns.set_preferred_prefix_for_namespace,
                          "a:b:c", "notaprefix")

        self.assertTrue(ns.is_valid())


    def test_schema_locations(self):
        ns = NamespaceSet()
        ns.add_namespace_uri("a:b:c", "abc", "sc:he:ma")

        self.assertEqual(ns.get_schema_location("a:b:c"), "sc:he:ma")

        self.assertRaises(mixbox.namespaces.ConflictingSchemaLocationError,
                          ns.set_schema_location, "a:b:c", "other:schemaloc")
        self.assertRaises(mixbox.namespaces.ConflictingSchemaLocationError,
                          ns.add_namespace,
                          Namespace("a:b:c", "abc", "other:schemaloc"))
        self.assertRaises(mixbox.namespaces.ConflictingSchemaLocationError,
                          ns.add_namespace_uri,
                          "a:b:c", "abc", "other:schemaloc")
        self.assertRaises(mixbox.namespaces.NamespaceNotFoundError,
                          ns.set_schema_location, "does:not:exist", "sc:he:ma")
        self.assertRaises(mixbox.namespaces.NamespaceNotFoundError,
                          ns.get_schema_location, "does:not:exist")

        ns.set_schema_location("a:b:c", "sc:he:ma2", True)
        self.assertEqual(ns.get_schema_location("a:b:c"), "sc:he:ma2")

        # test schema location merging; these should not raise exceptions
        ns.add_namespace_uri("a:b:c", "abc", None)
        self.assertEqual(ns.get_schema_location("a:b:c"), "sc:he:ma2")

        ns.add_namespace_uri("d:e:f", "def", None)
        ns.add_namespace_uri("d:e:f", "def", "def:schema")
        self.assertEqual(ns.get_schema_location("d:e:f"), "def:schema")

        self.assertTrue(ns.is_valid())

    def test_maps(self):
        ns = NamespaceSet()
        ns.add_namespace_uri("a:b:c", "abc", "abcschema")
        ns.add_prefix("a:b:c", "abc2")
        ns.add_namespace_uri("d:e:f", "def", "defschema")
        ns.set_preferred_prefix_for_namespace("d:e:f", None)

        self.assertEqual(ns.get_uri_prefix_map(),
                         {
                            "a:b:c": "abc",
                            "d:e:f": "def"
                         })
        self.assertEqual(ns.get_prefix_uri_map(),
                         {
                             "abc": "a:b:c",
                             "def": "d:e:f"
                         })

        # The map functions require all namespaces to have at least one
        # prefix (non-None).
        ns.add_namespace_uri("g:h:i", None, None)
        self.assertRaises(mixbox.namespaces.NoPrefixesError,
                          ns.get_prefix_uri_map)
        self.assertRaises(mixbox.namespaces.NoPrefixesError,
                          ns.get_uri_prefix_map)

        self.assertEqual(ns.get_uri_schemaloc_map(),
                         {
                             "a:b:c": "abcschema",
                             "d:e:f": "defschema"
                         })

        # If a preferred prefix is None, one of the other prefixes is chosen.
        # The choice is unpredictable.
        ns.add_prefix("g:h:i", "ghi1")
        ns.add_prefix("g:h:i", "ghi2")
        ns.add_prefix("g:h:i", "ghi3")

        uri_pfx_map = ns.get_uri_prefix_map()
        self.assertTrue(uri_pfx_map["g:h:i"] in ("ghi1", "ghi2", "ghi3"))

        pfx_uri_map = ns.get_prefix_uri_map()
        self.assertTrue("ghi1" in pfx_uri_map or
                        "ghi2" in pfx_uri_map or
                        "ghi3" in pfx_uri_map)

        self.assertTrue(ns.is_valid())

    # For verifying the overall format of the xmlns string.  It's in two parts,
    # 'cause I need to get the inner whitespace separation right.  The basic
    # format is <re>(\s+<re>)*, where the <re> part is the same regex.  I
    # didn't want to duplicate the whole thing inside one big regex, so it's
    # factored out.
    ONE_XMLNS_RE_NO_CAP = r"""
                               xmlns(?::\w+)?    # prefix
                               \s*=\s*           # equals
                               "[^"]*"           # value
                           """

    XMLNS_RE_NO_CAP = re.compile(
        r"""^\s*%s(?:\s+%s)*\s*$""" % (ONE_XMLNS_RE_NO_CAP, ONE_XMLNS_RE_NO_CAP),
        re.X
    )

    # For pulling out the individual namespace declarations
    XMLNS_RE = re.compile(r"""
                              xmlns(:\w+)?                # prefix
                              \s*=\s*                     # equals
                              "([^"]*)"\s+                # value
                           """, re.X)

    # For verifying the overall format of the schemalocation string.  This
    # matches the whole thing, and has no captures.
    SCHEMALOC_RE_NO_CAP = re.compile(r"""
                                         ^xsi:schemaLocation\s*=\s*"\s*
                                         (?:\S+\s+\S+)       # first ns/loc pair
                                         (?:\s+\S+\s+\S+)*   # rest of ns/loc pairs
                                         \s*"$
                                      """, re.X)

    def __get_contents_of_xmlns_string(self, xmlns_string):
        """Converts an xml namespace declaration string to a NamespaceSet."""
        ns = NamespaceSet()
        for m in self.XMLNS_RE.finditer(xmlns_string):
            pfx  = m.group(1)
            uri  = m.group(2)
            if pfx and pfx[0] == ":": # drop leading colons if any
                pfx = pfx[1:]
            ns.add_namespace_uri(uri, pfx)
        return ns

    def __get_schema_location_pairs(self, schemaloc_string):
        """Creates a uri->schemaloc dict with the pairs from the schemaloc
        string.  Assumes schemaloc_string matches SCHEMALOC_RE_NO_CAP."""
        m = re.match(r'^xsi:schemaLocation="\s*', schemaloc_string)

        # start of pairs within schemaloc_string
        schemaloc_start = len(m.group(0))

        m = re.search(r'\s*"$', schemaloc_string)

        # (1-past) end of pairs within the schemaloc_string
        schemaloc_end = m.start(0)

        uris = re.split(r"\s+", schemaloc_string[schemaloc_start:schemaloc_end])

        self.assertEqual(len(uris) % 2, 0)  # require an even number of uris

        return dict(zip(uris[::2], uris[1::2]))

    def __namespaceset_equal_uris_and_prefixes(self, ns1, ns2):
        """I need a NamespaceSet equality check which ignores schema locations
        and preferred prefixes."""
        if len(ns1) != len(ns2):
            return False
        for ns_uri in ns1.namespace_uris:
            if not ns2.contains_namespace(ns_uri):
                return False
            if ns1.get_prefixes(ns_uri) != ns2.get_prefixes(ns_uri):
                return False
        return True

    def test_strings(self):
        ns = NamespaceSet()
        ns.add_namespace_uri("a:b:c", "abc", "abcschema")
        ns.add_prefix("a:b:c", "abc2")
        ns.add_namespace_uri("d:e:f", "def", "defschema")
        ns.add_namespace_uri("g:h:i", None)

        # Preferred prefixes only; "abc2" should not be a declared prefix for
        # a:b:c.
        xmlns_string = ns.get_xmlns_string()
        m = self.XMLNS_RE_NO_CAP.match(xmlns_string)
        self.assertNotEqual(m, None, "Invalid XML namespace declaration format")

        ns2 = self.__get_contents_of_xmlns_string(xmlns_string)
        self.assertEqual(len(ns2), 3)

        self.assertTrue(ns2.contains_namespace("a:b:c"))
        self.assertTrue(ns2.contains_namespace("d:e:f"))
        self.assertTrue(ns2.contains_namespace("g:h:i"))

        self.assertEqual(ns2.get_prefixes("a:b:c"), set(["abc"]))
        self.assertEqual(ns2.get_prefixes("d:e:f"), set(["def"]))
        self.assertEqual(len(ns2.get_prefixes("g:h:i")), 0)

        self.assertEqual(ns2.preferred_prefix_for_namespace("a:b:c"), "abc")
        self.assertEqual(ns2.preferred_prefix_for_namespace("d:e:f"), "def")
        self.assertEqual(ns2.preferred_prefix_for_namespace("g:h:i"), None)

        # Now, gimme all the prefixes
        xmlns_string = ns.get_xmlns_string(preferred_prefixes_only=False)
        m = self.XMLNS_RE_NO_CAP.match(xmlns_string)
        self.assertNotEqual(m, None, "Invalid XML namespace declaration format: " +
                             xmlns_string)

        ns2 = self.__get_contents_of_xmlns_string(xmlns_string)
        self.assertTrue(self.__namespaceset_equal_uris_and_prefixes(ns, ns2))

        schemaloc_string = ns.get_schemaloc_string()
        m = self.SCHEMALOC_RE_NO_CAP.match(schemaloc_string)
        self.assertNotEqual(m, None,
                             "Invalid XML schema location declaration format")
        schemaloc_dict = self.__get_schema_location_pairs(schemaloc_string)

        self.assertEqual(schemaloc_dict,
                         {
                             "a:b:c": "abcschema",
                             "d:e:f": "defschema"
                         })

        # Uh oh, another namespace with no prefixes... this NamespaceSet can't
        # yield an xmlns declaration string anymore.
        ns.add_namespace_uri("j:k:l", None)
        self.assertRaises(mixbox.namespaces.TooManyDefaultNamespacesError,
                          ns.get_xmlns_string)

    def test_subset(self):
        ns = NamespaceSet()
        ns.add_namespace_uri("a:b:c", "abc", "abcschema")
        ns.add_namespace_uri("d:e:f", "def", "defschema")

        correct_subns = NamespaceSet()
        correct_subns.add_namespace_uri("a:b:c", "abc", "abcschema")

        subns = ns.subset(("a:b:c",))
        self.assertEqual(subns, correct_subns)

    def test_import(self):
        ns = NamespaceSet()
        ns.add_namespace_uri("a:b:c", "abc", "abcschema")

        imported_ns = NamespaceSet()
        imported_ns.add_namespace_uri("d:e:f", "def", "defschema")

        union_ns = NamespaceSet()
        union_ns.add_namespace_uri("a:b:c", "abc", "abcschema")
        union_ns.add_namespace_uri("d:e:f", "def", "defschema")

        ns.import_from(imported_ns)
        self.assertEqual(ns, union_ns)

        imported_ns2 = NamespaceSet()
        imported_ns2.add_namespace_uri("a:b:c", "abc2")
        # a:b:c is already in ns, replace=True, so this replaces ns's a:b:c
        # entry with (a copy of) imported_ns2's entry.
        ns.import_from(imported_ns2, True)

        self.assertEqual(ns.get_prefixes("a:b:c"), set(["abc2"]))
        self.assertEqual(ns.get_schema_location("a:b:c"), None)

        imported_ns3 = NamespaceSet()
        imported_ns3.add_namespace_uri("g:h:i", "def")
        self.assertRaises(mixbox.namespaces.DuplicatePrefixError,
                          ns.import_from, imported_ns3)

        self.assertTrue(ns.is_valid())

if __name__ == "__main__":
    unittest.main()
