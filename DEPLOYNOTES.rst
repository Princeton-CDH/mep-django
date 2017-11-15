.. _DEPLOYNOTES:

Deploy and Upgrade notes
========================

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
