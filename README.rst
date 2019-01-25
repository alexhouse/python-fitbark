python-fitbark
==============

.. image:: https://travis-ci.org/alexhouse/python-fitbark.svg?branch=master
   :target: https://travis-ci.org/alexhouse/python-fitbark
   :alt: Build Status
.. image:: https://coveralls.io/repos/alexhouse/python-fitbark/badge.png?branch=master
   :target: https://coveralls.io/r/alexhouse/python-fitbark?branch=master
   :alt: Coverage Status
.. image:: https://requires.io/github/alexhouse/python-fitbark/requirements.png?branch=master
   :target: https://requires.io/github/alexhouse/python-fitbark/requirements/?branch=master
   :alt: Requirements Status
.. image:: https://badges.gitter.im/alexhouse/python-fitbark.png
   :target: https://gitter.im/alexhouse/python-fitbark
   :alt: Gitter chat

FitBark API Python Client Implementation

For documentation: `http://python-fitbark.readthedocs.org/ <http://python-fitbark.readthedocs.org/>`_

Requirements
============

* Python 2.7+
* `python-dateutil`_ (always)
* `requests-oauthlib`_ (always)
* `Sphinx`_ (to create the documention)
* `tox`_ (for running the tests)
* `coverage`_ (to create test coverage reports)

.. _python-dateutil: https://pypi.python.org/pypi/python-dateutil/2.4.0
.. _requests-oauthlib: https://pypi.python.org/pypi/requests-oauthlib
.. _Sphinx: https://pypi.python.org/pypi/Sphinx
.. _tox: https://pypi.python.org/pypi/tox
.. _coverage: https://pypi.python.org/pypi/coverage/

To use the library, you need to install the run time requirements:

   sudo pip install -r requirements/base.txt

To modify and test the library, you need to install the developer requirements:

   sudo pip install -r requirements/dev.txt

To run the library on a continuous integration server, you need to install the test requirements:

   sudo pip install -r requirements/test.txt
