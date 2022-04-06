#!/usr/bin/env python

# Copyright (c) 2015 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import sys
from os.path import abspath, dirname, join

from setuptools import setup, find_packages

BASE_DIR = dirname(abspath(__file__))
VERSION_FILE = join(BASE_DIR, 'mixbox', 'version.py')


def get_version():
    with open(VERSION_FILE) as f:
        for line in f.readlines():
            if line.startswith("__version__"):
                version = line.split()[-1].strip('"')
                return version
        raise AttributeError("Package does not have a __version__")


with open('README.rst') as f:
    readme = f.read()

install_requires = ['python-dateutil', 'ordered-set']

py_maj, py_minor = sys.version_info[:2]
# lxml has dropped support for Python 2.6, 3.3 after version 4.2.6
if (py_maj, py_minor) == (2, 6) or (py_maj, py_minor) == (3, 3):
    install_requires.append('lxml>=2.2.3,<4.3.0')
# lxml has dropped support for Python 2.6, 3.3, 3.4 after version 4.4.0
elif (py_maj, py_minor) == (2, 6) or (py_maj, py_minor) == (3, 4):
    install_requires.append('lxml>=2.2.3,<4.4.0')
else:
    install_requires.append('lxml')

# Some required modules/packages don't exist in all versions of Python.
# Luckily, backports exist in PyPI.
backports = {
    # WeakMethod was introduced in Python 3.4
    "weakrefmethod>=1.0.3": "from weakref import WeakMethod",
    "importlib": "import importlib",
    "weakrefset": "from weakref import WeakSet"
}

for package, importstmt in backports.items():
    try:
        exec(importstmt)
    except ImportError:
        install_requires.append(package)

setup(
    name="mixbox",
    version=get_version(),
    author="The MITRE Corporation",
    author_email="cybox@mitre.org",
    description="Utility library for cybox, maec, and stix packages",
    long_description=readme,
    url="http://github.com/CybOXProject/mixbox",
    packages=find_packages(),
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ]
)
