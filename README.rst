mixbox
======

A library of common code leveraged by python-cybox, python-maec, and python-stix.

Developing
----------

To set up an environment to develop `mixbox`:

.. code:: bash

   # Create a new virtualenv
   $ mkvirtualenv mixbox

   # Change to this directory and install requirements
   $ cd /path/to/mixbox
   $ pip install -r requirements.txt

   # Install python-cybox, python-maec, and python-stix in "develop" mode.
   $ pip install -e /path/to/python-cybox
   $ pip install -e /path/to/python-maec
   $ pip install -e /path/to/python-stix


Then you can make changes to the `mixbox` library and ensure the test cases for
the corresponding projects continue to pass (using `tox` or `nosetests`).
