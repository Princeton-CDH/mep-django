.. _DEPLOYNOTES:

Deploy and Upgrade notes
========================

0.10 Members frontend
---------------------

* Switching from Mezzanine to Wagtail requires a manual migration *before*
  installing the new version to avoid migration dependency conflicts::

     python manage.py migrate pages zero

* Wagtail provides predefined groups for *Editor* and *Moderator*. Users
  who were previously in the *Content Editor* group should be added
  to one of these, and the *Content Editor* group should be removed.

* Run ``python manage.py setup_site_pages`` to create stub pages for all
  site content needed for main site navigation.

* The parasol package will automatically create a core if one does
  not already exist. It does require custom settings that are contained in
  ``solr_conf_sco`` be installed on the Solr instance under the ``configsets``
  directory prior to deployment. It also requires that ``CONFIGSET`` name is
  provided in the `default` dictionary under ``SOLR_CONNECTIONS``.
  See the sample Solr config in ``local_settings.py.sample``.


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
