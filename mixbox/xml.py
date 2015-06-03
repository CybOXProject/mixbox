# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

"""XML constants and functions"""

from lxml import etree

# XML NAMESPACES
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"

# XML TAGS
TAG_XSI_TYPE = "{%s}type" % NS_XSI
TAG_SCHEMALOCATION = "{%s}schemaLocation" % NS_XSI

# Acceptable values for XML booleans.
FALSE = (False, 'false', 0, '0')
TRUE = (True, 'true', 1, '1')


def is_element(obj):
    """Returns ``True`` if `obj` is an lxml ``Element``."""
    return isinstance(obj, etree._Element)  # noqa


def is_etree(obj):
    """Returns ``True`` if `obj` is an lxml ``ElementTree``."""
    return isinstance(obj, etree._ElementTree)  # noqa


def get_xml_parser(encoding=None):
    """Returns an ``etree.ETCompatXMLParser`` instance."""
    parser = etree.ETCompatXMLParser(
        huge_tree=True,
        remove_comments=True,
        strip_cdata=False,
        remove_blank_text=True,
        resolve_entities=False,
        encoding=encoding
    )

    return parser


def get_etree(doc, encoding=None):
    if is_etree(doc):
        return doc
    elif is_element(doc):
        return etree.ElementTree(doc)
    else:
        parser = get_xml_parser(encoding=encoding)
        return etree.parse(doc, parser=parser)


def get_etree_root(doc, encoding=None):
    """Returns an instance of lxml.etree._Element for the given `doc` input.

    Args:
        doc: The input XML document. Can be an instance of
            ``lxml.etree._Element``, ``lxml.etree._ElementTree``, a file-like
            object, or a string filename.
        encoding: The character encoding of `doc`. If ``None``, an attempt
            will be made to determine the character encoding by the XML
            parser.

    Returns:
        An ``lxml.etree._Element`` instance for `doc`.

    Raises:
        IOError: If `doc` cannot be found.
        lxml.ParseError: If `doc` is a malformed XML document.

    """
    tree = get_etree(doc, encoding)
    root = tree.getroot()

    return root


def get_schemaloc_pairs(node):
    """Parses the xsi:schemaLocation attribute on `node`.

    Returns:
        A list of (ns, schemaLocation) tuples for the node.

    Raises:
        KeyError: If `node` does not have an xsi:schemaLocation attribute.

    """
    schemalocs = node.attrib[TAG_SCHEMALOCATION]
    l = schemalocs.split()
    return zip(l[::2], l[1::2])


