.. _DEPLOYNOTES:

Deploy and Upgrade notes
========================

0.21
----

After this version is deployed, you should run ``import_figgy_cards``
to migrate old pudl image urls in Bibliography and Footnote records to
use the new objects in PUL's Figgy. The CSV file mapping old paths
to new Figgy ids is included as a fixture for convenience::

  python manage.py import_figgy_cards mep/accounts/fixtures/pudl-to-figgy-mapping.csv

0.17
----

* This release requires a reindex to update the birth and death year fields for
  use in faceting.

0.16
----

* This release requires a reindex to incorporate a bugfix for account partial
  date handling.

0.15
----

* This release requires a reindex to update the ``sex`` field for use in
  faceting.

0.14
----

* You must configure **OCLC_WSKEY** in ``localsettings.py`` before
  you can use the new ``reconcile_oclc`` manage command. You should
  also configure a TECHNICAL_CONTACT email address.

0.13
----

* Member search requires an updated solrconfig.xml. Copy
  `solr_conf/conf/solrconfig.xml` to your configured Solr configset
  directory.


0.12
----

* Index book data in Solr to populate the book browse::

  python manage.py index -i item


0.11
----

* Solr connection information should be configured in local settings as a
  **SOLR_CONNECTION**. See the sample Solr config in
  ``local_settings.py.sample``.

* The Solr configuration in the ``solr_conf`` directory must be installed
  on the Solr server the ``configsets``  directory prior to deployment
  with a name matching the **CONFIGSET** in the **SOLR_CONNECTIONS**
  default configuration.  See `Solr Config Sets documentation <https://lucene.apache.org/solr/guide/6_6/config-sets.html#config-sets>`_ for more details.
  Possible sequence of commands, starting from the server where the
  mep-django codebase is checked out::

     scp -r mep-django/solr_config solr-server:sandco

  Then on the server where Solr is running::

     mkdir -p /var/lib/solr/data/configsets
     cp -r sandco /var/lib/solr/data/configsets/
     chown solr:solr -R /var/lib/solr/data/configsets

* After the configset is in place on the server, run ``solr_schema`` to
  configure the configured Solr core. This command will create the core
  with the configured **CONFIGSET** if the core does not already exist::

  python manage.py solr_schema

* Index member data into Solr::

  python manage.py index

0.10
----

* Switching from Mezzanine to Wagtail requires a manual migration *before*
  installing the new version to avoid migration dependency conflicts::

     python manage.py migrate pages zero

* Wagtail provides predefined groups for *Editor* and *Moderator*. Users
  who were previously in the *Content Editor* group should be added
  to one of these, and the *Content Editor* group should be removed.

* Run ``python manage.py setup_site_pages`` to create stub pages for all
  site content needed for main site navigation.




0.6 Borrowing events and Title stubs
-------------------------------------

* Title stub records should be imported from XML using the
  **import_titles** manage command. The title XML file is located in
  https://github.com/Princeton-CDH/mapping-expatriate-paris and named
  `borrowed-titles.xml`.

* Borrowing events should be imported from XML using the
  **import_cards** manage command. Card XML files are located in
  https://github.com/Princeton-CDH/mapping-expatriate-paris under
  `transcriptions/cards/`. The command expects to be given the cards
  directory and will find all xml files under it, including in subdirectories.


0.3 Data Entry Improvements
---------------------------

* This update adds Mezzanine and enables the Django Site framework.
  The default Site should be configured after migrations complete.

0.2 Logbook admin
-----------------
* Logbook data should be imported from XML using the
**import_logbooks** manage command. The logbook XML is located in
https://github.com/Princeton-CDH/mapping-expatriate-paris under
`transcriptions/logbooks/*.xml`. The command tasks a list of files using
standard shell globbing. The import should be from the *develop* branch, which
has been cleaned up for import.


0.1 Personography admin
-----------------------

* The application must be configured with a GeoNames username and
  Mapbox access token in order to use GeoNames and Mapbox APIs.
* Personography data should be imported from XML using the
  **import_personography** manage command.  The personography XML
  for import is included in https://github.com/Princeton-CDH/mapping-expatriate-paris
  under `transcriptions/personography.xml`
  *NOTE*: import should be run from the *develop* branch, which has
  the latest version and has been cleaned up for import.
