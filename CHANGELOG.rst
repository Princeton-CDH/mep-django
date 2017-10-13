.. _CHANGELOG:

CHANGELOG
=========


0.1 Personography Admin & Import
--------------------------------

Initial release.  Provides administrative functionality for describing and
managing data about people associated with Sylvia Beach's lending library.


* As a global admin, I want a one-time import of data from the personography XML file so that I can manage person information in the database.
* As a global admin, when personography data is imported I want birth and death dates populated from the XML if available or else from VIAF if an id is available, so that dates will be complete and corrected dates will not be lost on import.
* As a content editor, I want to create and edit person records so that I can document biographical details about people associated with Sylvia Beach's lending library.
* As a content editor, I want to add and edit professions so I can categorize people associated with the library by their work.
* As a content editor, I want to add relationships between people in the database so that I can document known associates.
* As a content editor, when I'm viewing the list of people I want to see nationalities and number of associated addresses so I scan for records that need more data.
* As a content editor, I want to add URLs to a person record so I can document the person's wikipedia URL or other relevant websites.
* As a content editor, when I edit a person and add or change the VIAF ID, I want the birth and death dates in the system populated from data available in VIAF in order to make data entry more efficient.
* As a content editor, when I'm editing a person I want to add nationalities via autocomplete so the page loads faster and the list of countries don't take up as much space.
* As a content editor, when I'm editing a person I want to associate addresses via autocomplete so the page loads faster and the list of addresses don't take up as much space.
* As a content editor, when I edit an address with latitude and longitude I want to see a map so I can easily check that the coordinates.
* As a content editor, I want to add and edit countries so I can manage the list of countries available for documenting people’s nationalities.
* As a content editor, I want to add a new or edit an existing footnote and associate it with any other kind of record in the system so that I can document evidence related to assertions made elsewhere in the data.
* As a content editor, when I’m editing a person or address record, I want to be able to add footnotes on the same page so that I can easily document research about names and locations.
