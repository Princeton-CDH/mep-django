
mep-django
==========

.. sphinx-start-marker-do-not-remove


Python/Django web application for the `Shakespeare and Company Project
<https://shakespeareandco.princeton.edu/>`_,
a digital humanities project based on the archives of Sylvia Beach's
bookstore and lending library in Paris.

(This project was previously called "Mapping Expatriate Paris" or MEP).

Python 3.5 / Django 2.2 / Node 10.5.0 / MariaDB (MySQL) 5.5+ w/ timezone info

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3834179.svg
   :target: https://doi.org/10.5281/zenodo.3834179

.. image:: https://travis-ci.org/Princeton-CDH/mep-django.svg?branch=master
    :target: https://travis-ci.org/Princeton-CDH/mep-django
    :alt: Build status

.. image:: https://codecov.io/gh/Princeton-CDH/mep-django/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/Princeton-CDH/mep-django/branch/master
    :alt: Code coverage

.. image:: https://www.codefactor.io/repository/github/princeton-cdh/mep-django/badge
   :target: https://www.codefactor.io/repository/github/princeton-cdh/mep-django
   :alt: CodeFactor

.. image:: https://requires.io/github/Princeton-CDH/mep-django/requirements.svg?branch=master
     :target: https://requires.io/github/Princeton-CDH/mep-django/requirements/?branch=master
     :alt: Requirements Status

For specifics on the architecture and code, read `current release documentation <https://princeton-cdh.github.io/mep-django/>`_.

Development instructions
------------------------

Initial setup and installation:

- recommended: create and activate a python 3.5 virtualenv::

    virtualenv mep -p python3.5
    source mep/bin/activate

- Install required python dependencies::

    pip install -r requirements.txt
    pip install -r dev-requirements.txt

- Install javascript dependencies::

    npm install

- Compile static assets (css and javascript) with sourcemaps for development::

    npm run build:qa

- Copy sample local settings and configure for your environment::

    cp mep/local_settings.py.sample mep/local_settings.py

Remember to add a ``SECRET_KEY`` setting!

- Run the manage command to create your Solr core and configure the schema::

    python manage.py solr_schema

  The manage command will automatically reload the core to ensure schema
  changes take effect.

- Index all indexable content into Solr::

    python manage.py index

- optionally, you can populate the Wagtail CMS with stub pages for the main
  navigation::

    python manage.py setup_site_pages

- If running this application on MariaDB/MySQL, you must make sure that
  time zone definitions are installed. On most flavors of Linux/MacOS,
  you may use the following command, which will prompt
  for the database server's root password::

    mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root mysql -p

  If this command does not work, make sure you have the command line utilities
  for MariaDB/MySQL installed and consult the documentation for your OS for
  timezone info. Windows users will need to install a copy of the zoneinfo
  files.

  See `MariaDB <https://mariadb.com/kb/en/library/mysql_tzinfo_to_sql/>`_'s
  info on the utility for more information.

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


You must also configure Solr and install the configSet found under ``solr_conf``.
If a core does not exist, and the configSet is installed correctly, an appropriate
core will be made for you.

To install the configSet::


    (using root privileges for chown and permission as needed)
    cp -r solr_conf /path/to/solr/server/solr/configsets/sandco
    chown solr:solr -R /path/to/solr/server/solr/configsets/sandco

Note that this location will vary if your Solr instance has a separate data
folder. See ``DEPLOYNOTES`` for an example of that setup, which is commmon on
server installs of Solr.

You will also need to configure Django to use the Solr instance in
``local_settings.py``::


    SOLR_CONNECTIONS = {
        'default': {
            'URL': 'http://localhost:8983/solr/',
            'COLLECTION': 'sandcodev',
            'CONFIGSET': 'sandco'
        }
    }


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

    npm run test:unit


Accessibility Tests
-------------------

Automated accessibility tests run in travis using `pa11y-ci <https://github.com/pa11y/pa11y-ci>`_.
To run them locally, ensure that you have compiled frontend assets and a running
server::

    npm run build:prod
    python manage.py runserver --insecure

Then, run pa11y-ci to craw the sitemap and test for accessibility issues::

    npm run test:a11y

Running with ``DEBUG`` enabled will include the (inaccessible) Django
debug toolbar, so you'll probably want to turn it off.

Documentation
-------------

Documentation is generated using `sphinx <http://www.sphinx-doc.org/>`_.
To generate documentation, first install development requirements::

    pip install -r dev-requirements.txt

Then build documentation using the customized make file in the `docs`
directory::

    cd sphinx-docs
    make html

To build and publish documentation for a release, add the ``gh-pages`` branch
to the ``docs`` folder in your worktree::

  git worktree add -B gh-pages docs origin/gh-pages

In the ``sphinx-docs`` folder, use ``make docs`` to build the HTML documents
and static assets, add it to the docs folder, and commit it for publication on
Github Pages. After the build completes, push to GitHub from the ``docs`` folder.

License
-------
This project is licensed under the `Apache 2.0 License <https://github.com/Princeton-CDH/mep-django/blob/master/LICENSE>`_.

©2020 Trustees of Princeton University. Permission granted via Princeton Docket #21-3743-1 for distribution online under a standard Open Source license.
