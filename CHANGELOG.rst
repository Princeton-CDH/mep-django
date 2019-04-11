.. _CHANGELOG:

CHANGELOG
=========

0.13
----

* As a user, I want to search for library members by name or partial name so that I can find specific people I’m interested in.
* Updated results template & styles for book browse page

0.12
----

* As a user, I want the library member list paginated so that I don't have to browse through all the names at once.
* As a user, I want to browse a list of books so that I can see all the books known to have circulated through the library.
* As a user, I want the books list paginated so that I don't have to browse through all the titles at once.

* Updated JavaScript pipeline for TypeScript


0.11 Admin enhancements and initial Solr functionality
------------------------------------------------------
* As a data editor I want to document generic events related to books so that I can reflect the idiosyncrasies of non-standard borrowing events.
* As a data editor I want to search for footnote bibliography records by autocomplete so that I can more easily document events from the cards.
* As a content editor, I want to see a list of subscription events for people in the csv export so that I can make more informed decisions about merging people.
* As a user, I want to browse a list of library members sorted alphabetically by last name so that I can see all the names of people known to have patronized the library.

* Adds Solr functionality and configset installation instructions.
* Adds styles for member list search results.


0.10 Initial member list and Wagtail CMS functionality
------------------------------------------------------

Adds front-end styles and Webpack functionality, as well as Wagtail CMS.

* As a user, I want to see available demographic and library information (birth/death dates, nationality, membership dates, link to VIAF if available) for an individual library member, so that I can find out more about the person.
* As a content editor, I want to create and edit content pages on the site so that I can update text on the site when information changes


0.9 Add Purchase events to admin
----------------------------------

Exposes Purchase events for use on the Django admin

* As a content editor, I want to add and edit purchasing events so that I can add identified purchases visible on lending library cards.
* As a content editor, I need to add and edit partial dates for purchasing events so that I can record whatever portion of the date is available when the exact date is not known.
* As a content editor, I want to document the source of purchasing event information so that it will be linked to the card image for eventual public display.


0.8 Personography reports and other fixes
-----------------------------------------

Exports and a new verified flag for Person records to support personography
data work, including identifying records to be merged or demerged

* As a content admin, I want to export information about people in the database so I can work with it in other systems such as OpenRefine.
* As an admin, I want to generate a report of library members with large time gaps between events in their account history to identify records that may need demerging.
* As a content admin, I want to mark a person record as verified so that I can document that all the information in the record has been checked against the relevant archival sources.
* bugfix: merging into a logbook only person deletes account/lending card association if present
* bugfix: footnote editing causes a server error


0.7 Item and Person admin improvements
--------------------------------------

Adds filters and sorting options to the Person and Item admin views that enhance
content editor tasks, including tracking/sorting by update timestamps, filtering
Persons by role (member/creator/uncategorized), merging Persons without accounts,
searching items by database ID, and tracking BCE DateRanges for Person lifetimes.

* As a content editor, I want to see and sort on the date an item or person record was last updated so I can easily find recently edited records.
* As a content editor, I want to enter negative birth and death years so I can track biographical data for authors like Euripides.
* As a content editor, I want to search items by database id so that I can easily find items using the identifiers in the CSV export or notes.
* As a content editor, I want the option of merging people without accounts so that I can merge records for creators who were accidentally entered twice.
* As a content editor, I want to filter people in the personography by creator or library member so I can look at a subset of the people based on the kind of data work I'm doing.

0.6 Card import and basic item admin
------------------------------------

Provides editing functionality for borrowing events, including partial dates,
and basic bibliographic data for lending library item records.
Import script to migrate borrowing events and item information from
marked up XML lending card transcriptions into the database.


* As a global admin, I want a one-time import of regularized titles so that items can be managed in the database and associated with borrowing events.
* As a global admin, I want a one-time import of data from lending card XML files so that I can manage borrowing events and borrowed items in the database.
* As a global admin, I want the source of borrowing event information documented so that I can refer back to the item if necessary.
* As a content editor, I want to view and edit borrowing events so that I can review data imported from the cards and correct any errors.
* As a content editor, I need to view and edit partial dates for borrowing events so that I can see and record whatever portion of the date is available when the exact date is not known.
* As an content editor, I want to view borrowing event notes and edit purchase status on the list view so that I can quickly mark bought items that can't be autodetected on import.
* As a content editor, I want to create and edit library item records so that I can review, correct, and expand on basic metadata for imported library item stub data.
* As a content editor, I want to create and edit item creator types so that I can track item creator roles including author, translator, and editor.
* As an content editor, I want to see how many times an item has been borrowed and have an easy way to access all borrowing events for that item so I can investigate unclear titles and remove unused ones.
* As a global admin, I want a CSV export of bibliographic item data so that I can track data work and explore bulk data enhancements.
* As a content editor, I want to see an indicator if a person has an associated card so that I can distinguish library members with cards.
* bugfix: Admin menu order on the main dashboard is unstable

0.5 Data Entry Improvements II
------------------------------

Minor improvements to Django admin site functionality and data migration to
resolve Subscriptions with durations left in months as part of a previous
migration.

* As a content editor, when I merge two individuals, I want the notes field to include the date when the merge was completed, so that I can keep track of biographical work in the archive.
* As a content editor, I want to return to the page I was on when I started the process of merging people records so that I can continue working where I left off.
* As a content editor, I want to see a listing of reimbursements that an individual's account received, so that I can examine patterns in reimbursements as part of the lending library.

* One-time data migration to correct subscription durations not converted from months to days

0.4 Personography Merge
-----------------------

* As a content editor, I want to merge person records so that I can combine account records when I've identified duplicated people
* Removes now obsolete `import_logbooks` manage command.

0.3.1
-----
* Remove unneeded database backup from Ansible deploy.

0.3 Data Entry Improvements
---------------------------

Improvements to the admin interface to make data entry and content management
easier and more streamlined (particular emphasis on personography & accounts).

* As a global admin, I want addresses automatically associated with accounts in the logbook where possible to minimize the amount of manual cleanup required.
* As a content editor, I want to enter optional start and/or end dates for a person's addresses so I can document when they lived there if known.
* As a content editor, I want a one-time update to set people's gender based on titles where possible so that I don't have to edit all the records manually.
* As a content editor, I want the end date of a subscription automatically calculated based on start date and duration, so that I can enter subscriptions more quickly.
* As a content editor, I want event duplication to be prevented so I don't accidentally enter the same event twice.
* As a content editor, I want subscription event fields relabeled and ordered as they occur in the logbook so that I can add new subscriptions more efficiently.
* As a content editor, I want the reimbursement event form simplified so I can efficiently add new events.
* As a content editor, I want the personography list to include note previews so I can differentiate ambiguous names.
* As a content editor, I want a person's sort name to autopopulate when I type a single name with no spaces so that I don't have to retype it.
* As a content editor, I want an easy way to get from an account record to the associated person record so I can view and correct person details.
* As a content editor, I need a way to distinguish people with the same name when I'm selecting a person via autocomplete.
* As a content editor, I want currency for all events to default to "Franc" so that I don't have to set it every time.
* As a content editor, I want to edit and add new subscription categories so that I can document them as I discover them.
* As a content editor, I want to see account information when I'm editing a person record so I have enough context to make decisions and find sources.
* As a content editor, I want to see if people in the personography are in the logbooks rather than just that they have an account, because it tells me what data is available for them.
* As a content editor, I want the account list to include first and last known events dates so I can easily see membership timeline.
* As a content editor, when I'm editing accounts I want subscription and reimbursement sections to be open by default so I don't have to click to view membership dates.
* As a content editor, I want the event list to display type before notes so I can easily scan and differentiate events.
* As a content editor, I want project-specific data sections displayed first on the admin dashboard so I can easily get to the data I need to work with.

Known issues
~~~~~~~~~~~~

* Customized ordering on admin dashboard is not consistently displayed as configured.


0.2 Logbook Admin & Import
--------------------------

Admin functionality and data release. Provides administrative functionality for
describing and managing data related to the logbooks for Sylvia Beach's lending
library and their associated accounts.

* As a global admin, I want a one-time import of data from the logbook XML files so that I can manage lending library account and subscription information in the database.
* As a content editor, I want to see an indicator if a person has an account associated so that I can distinguish library members from others associated with the library.
* As a content editor, I want to create and edit account records so I can track how people associated with the library.
* As a content editor, I want to add and edit subscription information so I can track how and when members interacted with the library.
* As a content editor, I want to be able to view subscription events associated with an account so that I can see activity relating to an account at a glance.
* As a content editor, I want to be be able to see information about deposits refunded so that I can learn more about the habits of Beach and her clerks.
* As a content editor, I want to be able to see a listing of all events (regardless of type), so that I can look up their generic fields and any non-standard types that do not have a subcategory such as overdue notices.


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
