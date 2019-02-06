
mep-django
==========

.. sphinx-start-marker-do-not-remove


Python/Django web application for the `Shakespeare and Company Lending Library Project
<https://cdh.princeton.edu/projects/shakespeare-and-company-lending-library-project/>`_,
which examines the archives of Sylvia Beach's Shakespeare and Company lending library.
See also XML transcriptions for the materials on GitHub `mapping-expatriate-paris
<https://github.com/Princeton-CDH/mapping-expatriate-paris>`_.  (This project
was previously called "Mapping Expatriate Paris" or MEP).

See the preliminary `project website <http://mep.princeton.edu/>`_ for more details.

Python 3.5 / Django 1.11 / Node 10.5.0

.. image:: https://travis-ci.org/Princeton-CDH/mep-django.svg?branch=master
    :target: https://travis-ci.org/Princeton-CDH/mep-django
    :alt: Build status

.. image:: https://codecov.io/gh/Princeton-CDH/mep-django/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/Princeton-CDH/mep-django/branch/master
    :alt: Code coverage

.. image:: https://landscape.io/github/Princeton-CDH/mep-django/master/landscape.svg?style=flat
   :target: https://landscape.io/github/Princeton-CDH/mep-django/master
   :alt: Code Health

.. image:: https://requires.io/github/Princeton-CDH/mep-django/requirements.svg?branch=master
     :target: https://requires.io/github/Princeton-CDH/mep-django/requirements/?branch=master
     :alt: Requirements Status

`Current release documentation <https://princeton-cdh.github.io/mep-django/>`_.

Development instructions
------------------------

Initial setup and installation:

- recommended: create and activate a python 3.5 virtualenv::


    virtualenv mep -p python3.5
    source mep/bin/activate

- pip install required python dependencies::


    pip install -r requirements.txt
    pip install -r dev-requirements.txt

- npm install javascript dependencies::


    npm install

- compile static assets (css and javascript) with sourcemaps for development::


    npm run build:qa

- copy sample local settings and configure for your environment::


    cp mep/local_settings.py.sample mep/local_settings.py

Remember to add a ``SECRET_KEY`` setting!


Note that the admin index page will not reflect some changes without a manual
update - you will need to edit ``mep/dashboard.py`` to control the display and
ordering of admin items. More information is available in the `django-admin-tools
docs <http://django-admin-tools.readthedocs.io/en/latest/dashboard.html#>`_.

If you make changes to js or scss files and need to rebuild static assets::


    npm run build:qa

This will compile and minify all assets to ``static/`` with sourcemaps.
Alternatively, to run a production build without sourcemaps, you can use::

    npm run build:prod

Finally, for iterative frontend development, you can activate a webpack dev
server with hot reload using::


    npm start

Switching between the webpack dev server and serving from ``static/`` requires a
restart of your Django dev server to pick up the changed file paths.


Unit Tests
----------

Python unit tests are written with `py.test <http://doc.pytest.org/>`__ but use
Django fixture loading and convenience testing methods when that makes
things easier. To run them, first install development requirements::

    pip install -r dev-requirements.txt

Run tests using py.test::

    py.test

Javascript unit tests are written with `jest <https://jestjs.io/>`__. To run
them::

    npm run unit


Documentation
-------------

Documentation is generated using `sphinx <http://www.sphinx-doc.org/>`__
To generate documentation, first install development requirements::

    pip install -r dev-requirements.txt

Then build documentation using the customized make file in the `docs`
directory::

    cd sphinx-docs
    make html

When building for a release ``make docs`` will create a folder called ``docs``,
build the HTML documents and static assets, and force add it to the commit for
use with Github Pages.

License
-------
This project is licensed under the `Apache 2.0 License <https://github.com/Princeton-CDH/mep-django/blob/master/LICENSE>`_.
