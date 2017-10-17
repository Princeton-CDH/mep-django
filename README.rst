
mep-django
==========

.. sphinx-start-marker-do-not-remove


This Github repository houses the Django web interface of the `Mapping Expatriate
Paris <https://github.com/Princeton-CDH/mapping-expatriate-paris>`_ project, which
examines the archives of Sylvia Beach's Shakespeare and Company lending library.

See the project's `page <http://mep.princeton.edu/>`_ for more details.

Python 3.5 / Django 1.11

.. image:: https://travis-ci.org/Princeton-CDH/mep-django.svg?branch=develop
    :target: https://travis-ci.org/Princeton-CDH/mep-django
    :alt: Build status

.. image:: https://codecov.io/gh/Princeton-CDH/mep-django/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/Princeton-CDH/mep-django/branch/develop
    :alt: Code coverage

.. image:: https://landscape.io/github/Princeton-CDH/mep-django/develop/landscape.svg?style=flat
   :target: https://landscape.io/github/Princeton-CDH/mep-django/develop
   :alt: Code Health

.. image:: https://requires.io/github/Princeton-CDH/mep-django/requirements.svg?branch=develop
     :target: https://requires.io/github/Princeton-CDH/mep-django/requirements/?branch=develop
     :alt: Requirements Status


Development instructions
------------------------

Initial setup and installation:

- recommended: create and activate a python 3.5 virtualenv::


    virtualenv mep -p python3.5
    source mep/bin/activate

- pip install required python dependencies::


    pip install -r requirements.txt
    pip install -r dev-requirements.txt

- copy sample local settings and configure for your environment::


    cp mep/local_settings.py.sample mep/local_settings.py

Remember to add a ``SECRET_KEY`` setting!


Unit Tests
----------

Unit tests are written with `py.test <http://doc.pytest.org/>`__ but use
Django fixture loading and convenience testing methods when that makes
things easier. To run them, first install development requirements::

    pip install -r dev-requirements.txt

Run tests using py.test::

    py.test

Documentation
-------------

Documentation is generated using `sphinx <http://www.sphinx-doc.org/>`__
To generate documentation them, first install development requirements::

    pip install -r dev-requirements.txt

Then build documentation using the customized make file in the `docs`
directory::

    cd docs
    make html

When building for a release ``make docs`` will create a folder called ``docs``,
build the HTML documents and static assets, and force add it to the commit for
use with Github Pages.

License
-------
This project is licensed under the `Apache 2.0 License <https://github.com/Princeton-CDH/mep-django/blob/master/LICENSE>`_.
