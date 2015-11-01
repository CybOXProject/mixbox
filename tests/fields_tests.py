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


        entitylist = MockEntityList()
        entitylist_fields = list(fields.iterfields(MockEntityList))

        self.assertEqual(2, len(entity_fields))
        self.assertEqual(2, len(entitylist_fields))




if __name__ == "__main__":
    unittest.main()
