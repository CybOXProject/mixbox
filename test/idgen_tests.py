# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import unittest

from mixbox.namespaces import Namespace
from mixbox import idgen

TEST_NS = Namespace("http://some.namespace.com", "something", '')


class IDGeneratorMinimalTest(unittest.TestCase):

    def test_id(self):
        # Make sure we can create an ID with a minimum of effort.

        # TODO: actually delete the module and reimport it to make sure there
        # is nothing left over from another test.
        self.assertNotEqual(idgen.create_id(), "")


class IDGeneratorTest(unittest.TestCase):
    """Tests for the cybox.utils.IDGenerator class."""

    def setUp(self):
        method = idgen.IDGenerator.METHOD_INT
        self.generator = idgen.IDGenerator(method=method)

    def test_incrementing_ids(self):
        self.assertEqual(self.generator.create_id(), "example:guid-1")
        self.assertEqual(self.generator.create_id(), "example:guid-2")
        self.assertEqual(self.generator.create_id(), "example:guid-3")

    def test_namespace(self):
        self.generator.namespace = TEST_NS
        self.assertEqual(self.generator.create_id(),
                         TEST_NS.prefix + ":guid-1")

    def test_prefix(self):
        prefix = "some_object"
        id_ = self.generator.create_id(prefix)
        self.assertEqual(id_, "example:" + prefix + "-1")

    def test_invalid_method(self):
        self.assertRaises(idgen.InvalidMethodError,
                          idgen.IDGenerator,
                          TEST_NS,
                          "invalid method")


class IDGeneratorModuleTest(unittest.TestCase):
    """Tests for the cybox.utils module's IDGenerator"""

    def setUp(self):
        # Reset the generator's count before each test
        idgen.set_id_method(idgen.IDGenerator.METHOD_INT)
        gen = idgen._get_generator()
        gen.next_int = 1
        idgen.set_id_namespace(TEST_NS)

    def test_namespace(self):
        self.assertEqual(idgen.create_id(), TEST_NS.prefix + ":guid-1")

    def test_prefix(self):
        prefix = "some_object"
        id_ = idgen.create_id(prefix)
        self.assertEqual(id_, TEST_NS.prefix + ":" + prefix + "-1")

    def test_get_id_namespace(self):
        self.assertEqual(idgen.get_id_namespace(), TEST_NS.name)
        self.assertEqual(idgen.get_id_namespace_prefix(), TEST_NS.prefix)
        self.assertEqual(idgen.get_id_namespace_alias(), TEST_NS.prefix)


if __name__ == "__main__":
    unittest.main()
