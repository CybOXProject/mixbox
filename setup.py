# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

from os.path import abspath, dirname, join
from setuptools import setup, find_packages

INIT_FILE = join(dirname(abspath(__file__)), 'mixbox', '__init__.py')

def get_version():
    with open(INIT_FILE) as f:
        for line in f.readlines():
            if line.startswith("__version__"):
                version = line.split()[-1].strip('"')
                return version
        raise AttributeError("Package does not have a __version__")

with open('README.rst') as f:
    readme = f.read()

install_requires = ['six>=1.9.0', 'python-dateutil', 'weakrefset']

extras_require = {
    'docs': [
        'Sphinx==1.2.1',
        # TODO: remove when updating to Sphinx 1.3, since napoleon will be
        # included as sphinx.ext.napoleon
        'sphinxcontrib-napoleon==0.2.4',
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
