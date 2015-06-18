# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

"""
Common routines for working with data.
"""

from .vendor import six


def is_sequence(value):
    """
    Determine if a value is a sequence type.

    Returns:
      ``True`` if `value` is a sequence type (e.g., ``list``, or ``tuple``).
      String types will return ``False``.

    NOTE: On Python 3, strings have the __iter__ defined, so a simple hasattr
    check is insufficient.
    """
    return (hasattr(value, "__iter__") and not
            isinstance(value, (six.string_types, six.binary_type)))
