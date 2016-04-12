# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import unittest

from mixbox import fields
from mixbox.entities import Entity, EntityList


class MockEntity(Entity):
    foo = fields.TypedField("foo")
    bar = fields.TypedField("bar")


class MockEntityList(EntityList):
    foos = fields.TypedField("foo", MockEntity, multiple=True)
    bar  = fields.TypedField("bar")  # A regular TypedField


class TestTypedField(unittest.TestCase):

    def test_names(self):
        # The actual type is not important for this test
        a = fields.TypedField("Some_Field", None)
        self.assertEqual("Some_Field", a.name)
        self.assertEqual("some_field", a.key_name)

        a = fields.TypedField("From", None)
        self.assertEqual("From", a.name)
        self.assertEqual("from", a.key_name)


    def test_iterfields(self):
        entity_fields     = list(fields.iterfields(MockEntity))

        # Create an instance of MockEntityList because there had been a
        # bug where the number of typed_fields reported in iterfields()
        # grew each time we created an instance of the Entity.
        entitylist = MockEntityList()
        entitylist_fields = list(fields.iterfields(MockEntityList))

        self.assertEqual(2, len(entity_fields))
        self.assertEqual(2, len(entitylist_fields))


    def test_unset(self):
        class UnsetField(fields.TypedField):
            pass

        class TestEntity(Entity):
            foo = UnsetField("foo")
            bar = fields.TypedField("bar")


        entity = TestEntity()
        entity.foo = "test"
        entity.bar = "test"

        self.assertEqual(entity.foo, "test")
        self.assertEqual(entity.bar, "test")

        fields.unset(entity, UnsetField)
        self.assertEqual(entity.foo, None)    # UnsetField has been unset
        self.assertEqual(entity.bar, "test")  # TypedField wasn't touched

        fields.unset(entity)
        self.assertEqual(entity.foo, None)  # All TypedFields unset
        self.assertEqual(entity.bar, None)  # All TypedFields unset


    def test_find(self):
        class FindEntity(Entity):
            foo = fields.TypedField("foo")
            multiple = fields.TypedField("foo", multiple=True)
            key_name = fields.TypedField("foo", multiple=True, key_name="key")

        entity = FindEntity()

        foos   = fields.find(entity, name="foo")
        self.assertEqual(len(foos), 3)

        multiples = fields.find(entity, multiple=True)
        self.assertEqual(len(multiples), 2)

        multiple_foos = fields.find(entity, name="foo", multiple=True)
        self.assertEqual(len(multiple_foos), 2)

        key_names = fields.find(entity, key_name="key")
        self.assertEqual(len(key_names), 1)

        miss = fields.find(entity, name="notfound")
        self.assertEqual(len(miss), 0)


if __name__ == "__main__":
    unittest.main()
