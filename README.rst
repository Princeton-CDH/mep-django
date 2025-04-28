
mep-django
==========

.. sphinx-start-marker-do-not-remove


Python/Django web application for the `Shakespeare and Company Project
<https://shakespeareandco.princeton.edu/>`_,
a digital humanities project based on the archives of Sylvia Beach's
bookstore and lending library in Paris.

(This project was previously called "Mapping Expatriate Paris" or MEP).

Python 3.12 / Django 5 / Node 18 / Postgresql 14 / Solr 9

.. image:: https://github.com/Princeton-CDH/mep-django/workflows/unit_tests/badge.svg
    :target: https://github.com/Princeton-CDH/mep-django/actions?query=workflow%3Aunit_tests
    :alt: Unit Test status

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3834179.svg
   :target: https://doi.org/10.5281/zenodo.3834179

.. image:: https://codecov.io/gh/Princeton-CDH/mep-django/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/Princeton-CDH/mep-django/branch/main
    :alt: Code coverage

.. image:: https://www.codefactor.io/repository/github/princeton-cdh/mep-django/badge
   :target: https://www.codefactor.io/repository/github/princeton-cdh/mep-django
   :alt: CodeFactor

For specifics on the architecture and code, read `current release documentation <https://princeton-cdh.github.io/mep-django/>`_.

Development instructions
------------------------

Initial setup and installation:

- Recommended: create and activate a python virtual environment using the
python version in `.python-version` using `pyenv <https://github.com/pyenv/pyenv>`_.

   - `pyenv install` will install the specified version of python, if needed;
     `pyenv local` will report the configured version
   - Run `python -m venv env`  to create a new virtual environment named `env`
   - `source env/bin/activate` to activate the virtual environment

- Install required python dependencies::

    # install python dependencies, including dev dependencies
    pip install -e '.[dev]'

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

- Run the migrations::

    python manage.py migrate

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

Copy the project Solr configset in ``solr_conf`` into your solr server configset
directory. For a local install::

    cp -r solr_conf /path/to/solr/server/solr/configsets/shxco
    chown solr:solr -R /path/to/solr/server/solr/configsets/shxco

Create Solr collection with the configured configset (use create_core with
Solr standalone and create_collection with SolrCloud)::

    solr create_core -c shxco -n shxco

You will also need to configure Django to use the Solr instance in
``local_settings.py``::


    SOLR_CONNECTIONS = {
        'default': {
            'URL': 'http://localhost:8983/solr/',
            'COLLECTION': 'shxco_dev',
            'CONFIGSET': 'shxco'
        }
    }


Unit Tests
----------

Python unit tests are written with `py.test <http://doc.pytest.org/>`_ but use
Django fixture loading and convenience testing methods when that makes
things easier. To run them, first install development requirements::

    pip install -e '.[dev]'

Run tests using py.test::

    pytest

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

Setup pre-commit hooks
~~~~~~~~~~~~~~~~~~~~~~

If you plan to contribute to this repository, please run the following command::

    pre-commit install

This will add a pre-commit hook to automatically format python code with `black <https://github.com/psf/black>`_.

Because these styling conventions were instituted after multiple releases of development on this project, ``git blame`` may not reflect the true author of a given line. In order to see a more accurate ``git blame`` execute the following command::

    git blame <FILE> --ignore-revs-file .git-blame-ignore-revs

Or configure your git to always ignore styling revision commits::

    git config blame.ignoreRevsFile .git-blame-ignore-revs

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
This project is licensed under the `Apache 2.0 License <https://github.com/Princeton-CDH/mep-django/blob/main/LICENSE>`_.

©2024 Trustees of Princeton University. Permission granted via Princeton Docket #21-3743-1 for distribution online under a standard Open Source license.