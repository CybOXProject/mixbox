# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

"""
Common functions for dealing with exceptions and warnings.
"""

import contextlib


# https://pythonadventures.wordpress.com/2013/09/07/how-to-ignore-an-exception-the-elegant-way/
@contextlib.contextmanager
def ignored(*exceptions):
    """Context Manager for cleanly ignoring exceptions.

    For example:
        with ignored(OSError):
            os.unlink('somefile.txt')

    This already exists as `contextlib.ignored` in Python 3.4
    """
    try:
        yield
    except exceptions:
        pass
