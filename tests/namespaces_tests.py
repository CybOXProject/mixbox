# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import unittest

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


class TestNamespaceMap(unittest.TestCase):

    def test_set_semantics(self):
        nsset = NamespaceSet()
        self.assertEqual(0, len(nsset))

        ns1 = Namespace("http://example.com/", "example", "")
        nsset.add(ns1)
        self.assertEqual(1, len(nsset))

        # Adding the same namespace doesn't have an effect
        nsset.add(ns1)
        self.assertEqual(1, len(nsset))

        # Neither does adding a new namespace object that is "equal" to the
        # first.
        nsset.add(Namespace("http://example.com/", "example", ""))
        self.assertEqual(1, len(nsset))


if __name__ == "__main__":
    unittest.main()
