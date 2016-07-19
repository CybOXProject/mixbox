#!/usr/bin/env python

# Copyright (c) 2015 - The MITRE Corporation
# For license information, see the LICENSE.txt file

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

install_requires = ['lxml', 'python-dateutil', 'ordered-set']

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

extras_require = {
    'docs': [
        'Sphinx==1.3.1',
        'sphinx_rtd_theme==0.1.8',
    ],
    'test': [
        "nose==1.3.0",
        "tox==1.6.1"
    ],
}

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
    extras_require=extras_require,
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ]
)
