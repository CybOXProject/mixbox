# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import unittest
import copy

from mixbox.entities import Entity, EntityList
from mixbox import fields

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
            _contained_type = Foo

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


if __name__ == "__main__":
    unittest.main()
