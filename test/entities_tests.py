# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import unittest
import copy

from mixbox.entities import Entity, EntityList, NamespaceCollector
from mixbox import fields
from mixbox.vendor import six
import mixbox.namespaces

class TestEntity(unittest.TestCase):

    # https://github.com/CybOXProject/python-cybox/issues/246
    def test_untyped_multiple(self):

        # You can't set arbitrary attributes on an object().
        class Mock(object):
            pass

        class SomeEntity(Entity):
            _binding_class = Mock

            single = fields.TypedField("Single")
            multiple = fields.TypedField("Multiple", multiple=True)

        s = SomeEntity()
        s.single = "a"
        s.multiple = "a"

        self.assertEqual(str, type(s.single))
        self.assertEqual(list, type(s.multiple))

        s_obj = s.to_obj()
        s_dict = s.to_dict()

        self.assertEqual("a", s_obj.Single)
        self.assertEqual(["a"], s_obj.Multiple)

        self.assertEqual("a", s_dict['single'])
        self.assertEqual(["a"], s_dict['multiple'])

    def test_deepcopy(self):
        """Test that copy.deepcopy() doesn't blow up on simple cases.

        See Also:
            https://github.com/CybOXProject/mixbox/issues/19
        """
        class MockEntity(Entity):
            foo = fields.TypedField("foo")
            bar = fields.TypedField("bar")

        eorig = MockEntity()
        eorig.foo = "FOO"
        eorig.bar = "BAR"

        ecopy = copy.deepcopy(eorig)

        # Test that the values copied and that value retrieval works.
        self.assertEqual(ecopy.foo, eorig.foo)
        self.assertEqual(ecopy.bar, eorig.bar)

    def test_hash_and_equality(self):
        """Test for hashing and equality of Entity"""
        class Foo(Entity):
            name = fields.TypedField("Name", None)

            def __init__(self, name):
                super(Foo, self).__init__()
                self.name = name

            def __str__(self):
                return self.name

        foo1 = Foo("Alpha")
        foo2 = Foo("Beta")

        self.assertNotEqual(hash(foo1), hash(foo2))
        self.assertNotEqual(foo1, foo2)

        foo3 = Foo("Alpha")

        self.assertEqual(hash(foo1), hash(foo3))
        self.assertEqual(foo1, foo3)


class TestEntityList(unittest.TestCase):

    def test_remove(self):

        class Foo(Entity):
            name = fields.TypedField("Name", None)

            def __init__(self, name):
                super(Foo, self).__init__()
                self.name = name

            def __str__(self):
                return self.name

        class FooList(EntityList):
            foos = fields.TypedField("foo", type_=Foo, multiple=True)

        foo1 = Foo("Alpha")
        foo2 = Foo("Beta")
        foo3 = Foo("Gamma")

        foolist = FooList(foo1, foo2, foo3)

        self.assertEqual(3, len(foolist))

        for f in list(foolist):
            self.assertTrue(f in foolist)
            if f.name == "Beta":
                foolist.remove(f)
                self.assertEqual(f, Foo("Beta"))
                self.assertFalse(f is Foo("Beta"))

        self.assertEqual(2, len(foolist))


NSMAP = {
    "test:a": "a",
    "test:b": "b",
    "test:c": "c"
}


SCHEMALOCS = {
    "test:a": "/dev/null",
    "test:b": "/dev/null",
    "test:c": "/dev/null"
}


class A(Entity):
    _namespace = mixbox.namespaces.NS_XML_SCHEMA.name
    _XSI_TYPE = "a:AType"


class B(A):
    _namespace = mixbox.namespaces.NS_XML_SCHEMA_INSTANCE.name
    _XSI_TYPE = "b:BType"


class C(B):
    _namespace = mixbox.namespaces.NS_XLINK.name
    _XSI_TYPE = "c:CType"


class TestNamespaceCollector(unittest.TestCase):
    def test_nsinfo_collect(self):
        """Tests that the NamespaceInfo.collect() method correctly ascends the MRO
        of input objects.

        """
        nsinfo = NamespaceCollector()

        # Collect classes
        nsinfo.collect(C())

        # Parse collected classes
        nsinfo._parse_collected_classes()

        self.assertEqual(len(nsinfo._collected_namespaces), 3)  # noqa

    def test_namespace_collect(self):
        """Test that NamespaceInfo correctly pulls namespaces from all classes
        in an objects MRO.

        """
        nsinfo = NamespaceCollector()

        # Collect classes
        nsinfo.collect(C())

        # finalize the namespace dictionary
        nsinfo.finalize(ns_dict=NSMAP, schemaloc_dict=SCHEMALOCS)
        namespaces = nsinfo.binding_namespaces.keys()

        self.assertTrue(all(ns in namespaces for ns in six.iterkeys(NSMAP)))



if __name__ == "__main__":
    unittest.main()
