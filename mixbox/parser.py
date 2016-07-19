# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

from abc import ABCMeta, abstractmethod
from distutils.version import StrictVersion

from .exceptions import ignored
from .xml import get_etree_root, get_etree, get_schemaloc_pairs
from .vendor.six import iteritems


class UnknownVersionError(Exception):
    """A parsed document contains no version information."""
    pass


class UnsupportedVersionError(Exception):
    """A parsed document is a version unsupported by the parser."""

    def __init__(self, message, expected=None, found=None):
        super(UnsupportedVersionError, self).__init__(message)
        self.expected = expected
        self.found = found


class UnsupportedRootElementError(Exception):
    """A parsed document contains an unsupported root element."""

    def __init__(self, message, expected=None, found=None):
        super(UnsupportedRootElementError, self).__init__(message)
        self.expected = expected
        self.found = found


class EntityParser(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def supported_tags(self):
        """Return an iterable of supported document root tags (strings)."""

    @abstractmethod
    def get_version(self, root):
        """Return as a string the schema version used by the document root."""

    @abstractmethod
    def supported_versions(self, tag):
        """Return all the supported versions for a given tag."""

    @abstractmethod
    def get_entity_class(self, tag):
        """Return the class to be returned as the result of parsing."""

    def _get_version(self, root):
        """Return the version of the root element passed in.

        Args:
            root (etree.Element)

        Returns:
            distutils.StrictVersion

        Raises:
            UnknownVersionError
        """
        # Note: STIX and MAEC use a "version" attribute. To support CybOX, a
        # subclass will need to combine "cybox_major_version",
        # "cybox_minor_version", and "cybox_update_version".
        version = self.get_version(root)
        if version:
            return StrictVersion(version)

        raise UnknownVersionError(
            "Unable to determine the version of the input document. No "
            "version information found on the root element."
        )

    def _check_version(self, root):
        """Ensure the root element is a supported version.

        Args:
            root (etree.Element)

        Raises:
            UnsupportedVersionError
        """
        version = self._get_version(root)
        supported = [StrictVersion(x) for x in
                     self.supported_versions(root.tag)]

        if version in supported:
            return

        error = "Document version ({0}) not in supported versions ({1})"
        raise UnsupportedVersionError(
            message=error.format(version, supported),
            expected=supported,
            found=version
        )

    def _check_root_tag(self, root):
        """Check that the XML element tree has a supported root element.

        Args:
            root (etree.Element)

        Raises:
            UnsupportedRootElementError
        """
        supported = self.supported_tags()
        if root.tag in supported:
            return

        error = "Document root element ({0}) not one of ({1})"
        raise UnsupportedRootElementError(
            message=error.format(root.tag, supported),
            expected=supported,
            found=root.tag,
        )

    def parse_xml_to_obj(self, xml_file, check_version=True, check_root=True,
                         encoding=None):
        """Creates a STIX binding object from the supplied xml file.

        Args:
            xml_file: A filename/path or a file-like object representing a STIX
                instance document
            check_version: Inspect the version before parsing.
            check_root: Inspect the root element before parsing.
            encoding: The character encoding of the input `xml_file`.

        Raises:
            .UnknownVersionError: If `check_version` is ``True`` and `xml_file`
                does not contain STIX version information.
            .UnsupportedVersionError: If `check_version` is ``False`` and
                `xml_file` contains an unsupported STIX version.
            .UnsupportedRootElement: If `check_root` is ``True`` and `xml_file`
                contains an invalid root element.

        """
        root = get_etree_root(xml_file, encoding=encoding)

        if check_root:
            self._check_root_tag(root)

        if check_version:
            self._check_version(root)

        entity_class = self.get_entity_class(root.tag)
        entity_obj = entity_class._binding_class.factory()
        entity_obj.build(root)

        return entity_obj

    def parse_xml(self, xml_file, check_version=True, check_root=True,
                  encoding=None):
        """Creates a python-stix STIXPackage object from the supplied xml_file.

        Args:
            xml_file: A filename/path or a file-like object representing a STIX
                instance document
            check_version: Inspect the version before parsing.
            check_root: Inspect the root element before parsing.
            encoding: The character encoding of the input `xml_file`. If
                ``None``, an attempt will be made to determine the input
                character encoding.

        Raises:
            .UnknownVersionError: If `check_version` is ``True`` and `xml_file`
                does not contain STIX version information.
            .UnsupportedVersionError: If `check_version` is ``False`` and
                `xml_file` contains an unsupported STIX version.
            .UnsupportedRootElement: If `check_root` is ``True`` and `xml_file`
                contains an invalid root element.

        """

        xml_etree = get_etree(xml_file, encoding=encoding)
        entity_obj = self.parse_xml_to_obj(
            xml_file=xml_etree,
            check_version=check_version,
            check_root=check_root
        )

        xml_root_node = xml_etree.getroot()
        entity = self.get_entity_class(xml_root_node.tag).from_obj(entity_obj)

        # Save the parsed nsmap and schemalocations onto the parsed Entity
        entity.__input_namespaces__ = dict(iteritems(xml_root_node.nsmap))
        with ignored(KeyError):
            pairs = get_schemaloc_pairs(xml_root_node)
            entity.__input_schemalocations__ = dict(pairs)

        return entity
