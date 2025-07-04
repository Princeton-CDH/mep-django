CHANGELOG
=========

1.9
---

- bugfix: VIAF Autocomplete Not Working
- chore: Upgrade the python, Django, wagtail stack for S&Co website
- chore: Update or replace dependency on LoC django-tabular-export package
- chore: Migrate settings to django-split-settings

1.8
---

- Upgrade to solr 9
- Revisions to datapackage validation & readme script for 2.0 dataset publication

1.7.2
-----

- bugfix: include address location name in member address data export

1.7.1
-----

- Add `INCLUDE_ANALYTICS` to template context so Plausible analytics can be enabled

1.7
---

Revisions to data exports in preparation for 2.0 dataset publication:

- Address export files renamed `member_addresses` (both csv and json)
- Creator export files renamed `book_creators` (both csv and json)
- Address export manage command now does not include start and end dates by default,
with an optional flag to include them
- Address export includes care of person id and name, location name, and member names, sort names, and uris
- Nested information in JSON data exports is now grouped by entity
- Add support for Plausible analytics, configurable with PLAUSIBLE_ANALYTICS_SCRIPT and PLAUSIBLE_ANALYTICS_404s in django settings

1.6.2
-----

* bugfix: add an option to prevent VIAF birth/death dates from being populated
  on person record save when blank, so incorrect VIAF dates can be removed

1.6.1
-----

* Pin django-markdownify to 0.9.3 to avoid an incompatibility error with bleach in django-markdownify 0.9.4

1.6
---

* As a content editor, I want to batch import new data on books' genre, so that I can update multiple records with annotations made externally.
* As a content editor, I want to batch import authors/creator information, so that I can update multiple records with annotations made externally.
* As a content admin, I want to export information about creators from the database so I can work with the data using other tools.
* As a content admin, I want to export member addresses with more details in a separate file so I can more easily work with member locations.
* bugfix: viaf lookup for birth/death dates
* bugfix: admin geonames lookup
* data migration to populate person birth and death dates from VIAF where VIAF id set but dates are not

1.5.7
-----

* Upgrade to Python 3.8, Django 3.2, and Wagtail 5.1
* bugfix: anchor link to borrowing events in card table hidden by sticky table header
* bugfix: admin autocompletes incompatibility error with django-autocomplete-light upgrade
* bugfix: years for members with multi-year range membership and no other activity are reported incorrectly
* Setup pre-commit and applied black formatting to existing code

1.5.6
-----

* Revise footer to include ISSN, accommodate more About pages, and pull from Wagtail
* Add daily total to 100 years twitter review page; add times for up to 20 per day


1.5.5
-----

* Updated dataset metadata and scripts, including datapackage files, in support of dataset version 1.2

1.5.4
-----

* Update Bibliographies to reflect the name change of Princeton University's Special Collections
* Handle addresses without coordinates when generating members dataset
* Upgrade to django 3.0 and wagtail 2.10

1.5.3
-----

* Switch database backend from MySQL to PostgreSQL
* Upgrade to Solr 8
* Upgrade to Python 3.6

1.5.2
-----

* Rename "separate deposit" subscription event type to "separate payment"
* Allow multiple reimbursements for the same account on the same day as long as the amounts differ

1.5.1
-----

* bugfix: handle subscription events without duration in 100 years tweets

1.5
---
* As a content editor, I want to embed external content in editorial and other pages, so that I can include dynamic content in essays.
* Disabled person address inline in admin site to avoid associating addresses with people instead of accounts
* bugfix: correct event export to include subscription price/deposit amounts for separate deposit events


1.4.1
-----

Update book export so contributor fields are ordered based on admin-configured sort order (author first).

1.4
---


* As a data user, I want to see multiple source types and source citations when an event is documented in multiple sources, so that I can understand and access the sources for the data.
* As an events data user, I want borrowing duration available in days so that I can easily calculate and compare borrowing events with known durations.
* bugfix: saving subscriptions with unknown years in subsequent years no longer causes an error calculating duration
* data export scripts are now more efficient
* continuous integration testing moved from Travis-CI to GitHub Actions

1.3
---

* As a data export user, I want the event data export to include source type so I can easily see which events are from the logbooks, address books, or cards.
* As a data editor or dataset user, I want all source citations for all events so that I can tell which ones came from logbooks, address books, or cards.
* As a data editor, I need to enter subscriptions for the same person that start on the same date if they have different end dates, so I can track different subscriptions purchased at the same time.
* Include VIAF id in admin CSV download for people
* Rename subscription type "Other" to "Separate Deposit"
* Update tagline for sources in main menu
* bugfix: on the member list, member names that start with punctuation should sort based on first letter
* bugfix: handle events without titles on card detail pages
* bugfix: handle titles without years in 100 years tweets (fix duplicate period)

1.2.4
-----

* Fix 100 years tweets for generic events with event type indicated in notes
* Redact n-word in titles when generating tweets


1.2.3
-----

* Pin wagtail version to pre 2.10 for python 3.5 support

1.2.2
-----

* bugfix: fix membership graph so data and y-axis use the same linear scale
* bugfix: reindex books when related events (specifically borrows and purchases) are modified
* design fix: adjust author/title spacing mobile borrowing card view for authors with long names

1.2.1
-----

* Minor adjustments to 100 years tweet format
* design fix: set citation block to scroll horizontally on overflow (keep long urls from breaking mobile display)

1.2
---

* As an admin, when I change work slugs I want past slugs stored and used for redirects on public views so that links for edited works continue to resolve.
* New manage command to manage and post #100YearsAgoToday tweets, including an admin review page to check tweets before they are posted
* Revise data export logic in preparation for data publication
* Remove volume/issue list on individual book bibliography page
* bugfix: subscription amount on membership activities list only includes price paid, not deposit

1.1.1
-----

* bugfix: event footnotes can be edited in different places in django admin, which makes it easy to end up with duplicate footnotes
* bugfix: book search is over-emphasizing stopwords, especially in author names
* bugfix: Editions now sort on volume in numerical order after date
* design fix: line height for names on card gallery view
* design fix: correctly display irregular size images in card gallery view
* Added variant event type for periodical subscriptions


1.1
---

* As a user, I want to see larger size card images so that I can look at cards in more detail and decipher difficult handwriting.
* As a user, I want to see circulation information on book search and detail pages so I understand how much and when a book circulated.
* As a user, I want to see event labels for non-standard book events in the borrowing activity table and event data download so I know what the data represents.
* As a content editor, I want to add basic formatting to public notes so that I can differentiate titles from authors and dates.
* As a user I want to see addresses on member maps with arrondissements instead of postal codes, so that I see them in an historically accurate format.
* As a user, I want to filter on members with "Unidentified" nationality so I can see how many members do not have nationality documented and can find them.
* Match searches for author and member initials with and without spaces

other improvements
~~~~~~~~~~~~~~~~~~
* bugfix: arrondissement facet counts on member page never change
* bugfix: atypical card images are displayed incorrectly
* bugfix: display both names for joint accuonts on book circulation lists
* bugfix: member data export does not include postal code / arrondissement
* bugfix: member search results have blank aria-label
* bugfix: empty facets result in a 500 error on member search page
* accessibility: leaflet maps are scroll traps
* accessibiity: missing heading for home page
* design fix: correct placement for nationality link icon
* design fix: link styles for icons on the card gallery and card image viewer pages
* design fix: correct pacing for public notes on book pages
* design fix: make all the link styles 2px wide
* design fix: Breadcrumbs should show current page unless 4th level deep
* design fix: improve mobile display for borrowing and circulation activity pages

1.0.1
-----

* bugfix: correct the order for lending library cards
* bugfix: 500 error creating new person records
* bugfix: adjust admin person edit form and slug help text
* bugfix: wagtail paragraph block is missing custom feature list (blockquotes,
  superscript, etc)


1.0
---

This release makes the Books section available.

* As a user, when I'm viewing a single book I want an easy way to find all card images associated with that item so I can see where it's referenced in the archival materials.
* As a user, I want to see and toggle my active search filters so that I can see how they affect my search.
* As a user, when I'm browsing members I want to see membership years that show gaps in activity so that I'm not misled by what appears to be a longer continuous membership.
* As a user viewing a member biography page, I want to see membership dates that represent actual activity so that I'm not misled by what appears to be a longer continuous membership.
* As a user viewing borrowing activities for a single library member, I want to see issue number and date or volume number when known so I have better information about the item.
* As a user, I'd like to see an error indicator when a card image doesn't load so I can see that something is missing.
* As an admin, when I merge people I want unique identifiers stored and used for redirects on public views so that links for merged people continue to resolve.
* As a content editor, I want to edit the homepage tagline so that I can update it when necessary.
* re-enable books links in menus and remove login restrictions
* bugfix: result counters on search pages reset after page

Various improvements
~~~~~~~~~~~~~~~~~~~~
* XML sitemaps for member and book pages
* Last modified headers and conditional processing for member and book pages
* Better preview titles and descriptions in page metadata
* convert data export field names to use underscores instead of spaces
* Include membership years in member export and circulation years in book export
* Replace the breadcrumb home with the shakespeare icon on the third and fourth level pages
* Fix horizontal centering for breadcrumb text

0.29
----

* As a user, I want to sort works by title, author, publication date, or borrow count so that I can view and investigate by author, chronologically, or by popularity.
* As a user, I want to be able to search by titles of individual volumes of a multivolume book so that I can find the book by its parts.
* As a user, I want items automatically sorted by relevance if I have a keyword search term active and otherwise by title (by default), so that I see best matches first for keyword searches.
* As a user, I want to filter library items by circulation dates so that I can see items that circulated in the library in a particular time period.
* As a user, I want to see a chronological list of circulation activity for a single library item so that I can see which library members interacted with it.
* bugfix: search page dropdown shows incorrect page of results
* bugfix: single-day events on activity pages display as ranges on mobile display
* bugfix: mobile display of membership activity broken when dates are missing
* bugfix: navigating from detail pages back to search should return to the correct page of results
* bugfix: changing pages should scroll back to the top of search pages
* bugfix: django admin queries causing site timeout/unavailability

0.28.2
------

* bugfix: use Solr for django admin search for works, to avoid django admin
  database queries causing timeouts that bring down the site

0.28.1
------

* Disable book links in member borrowing activity until book pages are public
* Allow editors to use the same tags in linkable sections as paragraphs

0.28
----
* As an admin, I want to generate a data download for books so that I can deposit and version the data for others to use.
* As an admin, I want library items to have unique identifiers that can be included for use in URLs in the public site.
* As a user, I want to see bibliographic information (title, publication date, publisher, link to OCLC if available) for an individual library item, so that I can more accurately identify the item.
* As a user, I want to see notes about a person added by project team members so that I have more information about unusual library members.
* As a user viewing books, I want to see an indicator if there's a problem with the data and have a way to get more details, so that I know how to interpret the data.
* As data editor I want to search for footnote bibliography records by autocomplete so that I can more easily document accounts associated with cards.
* Chore: fix line spacing/leading on member pages for members with long/multiple names
* Bugfix: member card detail page should only show events for current member
* Bugfix: As an admin, I want to be able to enter duplicate events in the case where multiple purchases were made at the same time without title information.

0.27
----

* As a user, I want to search for library items by bibliographic metadata so that I can find specific items I’m interested in.
* As a user, I want the items list page updated as soon as I change search terms, filters, or results page so that I can refine my search without losing my place in the form and have results load more quickly.
* As a data editor, I want to enter months for periodical publication dates and non-numeric volumes when entering multivolume and periodical details.
* As a user viewing an individual work, I want to see a list of known issues (for periodical) or volumes (for multivolume works) so that I have more details about what items circulated.
* As an admin, I want to generate a data download of member information so that I can deposit and version the data for others to use.
* Revise events data export to exclude notes and use new edition display
* Updated to Django 2.2.10 and wagtail 2.8

0.26
----

* As an admin, I want to generate a data download for events so that I can deposit and version the data for others to use.
* As a user, when I'm viewing a single card image I want to navigate to any card images associated with the same member so that I can see all of their borrowing activity in context.

0.25
----

* As a data editor, I need to enter partially known dates for membership events so I can document memberships from sources where the exact date is not known.
* As a non-sighted user, I want to hear a description of visualizations embedded in essay content so that I can access these insights.
* As a user, I want to know when a member's card is available elsewhere so I can look beyond the site if needed.
* bugfix: document citation does not include author name even if author is associated with a document
* bugfix: editing library Location causes member detail pages to not load
* updates content and ordering of footer navigation
* restores blank card images in card image gallery and detail views

0.24
----

* As a user, I want to see a chronological list of book-related activities for a single library member so that I can see the complete history of book interactions for that person.
* As a user, I want to browse all card images with known events associated with a single member so that I can get an overview of their card activity.
* As a user, I want to see a large version of a single card image with associated events so that I can see the events in the context of the archival source.
* As a user, I want to see a rights statement for card images so that I know what I can do with them.
* As a user, I want to find members based on partial name matches so that I can find all variations of a name.
* As a user, I want sorting and search on member names to ignore case and work with or without accents so that I can find people more easily.
* As a content editor, I want to create linkable anchors in documents so that I can reference specific sections of my content on other pages.
* As a user, I want to see an indicator when my search doesn't return any results or something goes wrong so I know what happened.
* bugfix: account event_date_ranges doesn't properly handle ranges with end date but no start date
* bugfix: pages with breadcrumbs generate 500 error when schema.org is down
* bugfix: misconfigured signal handler causing 500 error on admin edits on addresses
* Numerous design and consistency improvements

0.23.1
------

* bugfix: event signal handler causing an error on admin edits


0.23
----

* As a user, I want to see a map of all of a member's known addresses so I can see where in Paris members lived.
* As a user, I want to browse a list of published editorial content so that I can see what analytical and scholarly content is available to read.
* As a user, I want to filter library members by arrondissement so I can find library members who lived in a particular part of Paris.
* As a user, I want to see a member's primary or best name prominently and also see other known names or so that I can recognize them and see how they were listed in the archival materials.
* As an admin, I want library members to have unique identifiers that can be used for URLs in the public site.
* As an admin, I want changes made to people and events in the admin interface to automatically update the member search, so that content in the search and admin interface stay in sync.
* As an admin, I want changes made to authors and books in the admin interface to automatically update the book search, so that content in the search and admin interface stay in sync.
* As an admin, I want changes made to card holders, card events, and thumbnails in the admin interface to automatically update the card search, so that content in the search and admin interface stay in sync.
* As a content admin, I want to view graphs showing an overview of library membership over time so that I can see how card and logbook data compares and so I can download an SVG to include in an essay.
* As a content admin, I want to add authors, publication date, and editors for essay pages so I can document the provenance of the content.
* As a content editor, I want to add new or edit existing editorial content so that I can publish and promote scholarly work related to the project.

* Rename 'sex' to 'gender' project-wide
* Update About and Sources landing pages so that tiles do not display any text description

0.22
----

* As a user, I want to browse a list of card images so that I can see digitized lending cards belonging to library members.
* As a user, I want the card image list paginated so that I don't have to browse through all the cards at once.
* As a user, I want the card image list page updated as soon as I change search terms, filters, or results page so that I can refine my search without losing my place in the form and have results load more quickly.
* As a user, I want to filter library members by nationality so that I can find all library members from a particular country.
* As a user, I want my filter options on the search page to be grouped into collapsible tabs so that I can find relevant filters more quickly.
* As a user, I want to see a visualization of a person’s library membership timeline so that I can get an overview of when and how they interacted with the library.

0.21
----

* As a user, I want to see an error page when the content I'm looking for isn't found so that I can choose a different path.
* As a user, I want to see an error page when the site is malfunctioning so that I can report the issue.
* As a data editor, I want the card image URLs in footnotes updated to resolve to Figgy after content is migrated so that I can access images in their new location.
* As data editor, I want to see thumbnails for bibliography and footnote records that have manifests and canvases attached, so I can check against the thumbnail and access the full size images.
* As a content admin, I want to select a featured image for content pages so I can give an idea of the content on the sources landing page and provide a visual preview for social media.
* As a content editor, I want to add SVG images to content pages so that I can include data visualizations and other scalable images.

* Temporarily configure public but incomplete urls to be login only
* Enable Google Analytics
* Content page text styles and updates
* Set up Content Security Policy

0.20
----

* As a user, I want to see a chronological list of membership activities for a single library member so that I can see the complete subscription activity for that person.

0.19
----

* As a data editor, I want to view and edit library items as works and associated editions so that I can have events related to the same item grouped but still document known editions.
* As an admin, I want to see how many times an item was purchased or associated with any event so that I can investigate unborrowed books more easily.
* As an admin, I want item borrow, purchase, and total event counts included in the CSV export so I can find and analyze books without associated events.
* bugfix: incorrect borrow counts in admin when search terms are active
* Removed XML import code (no longer needed, not maintaining)

0.18
----
* As a content editor I want to enter public notes for items and people so I can document details to be shown on the public site
* As a content editor, I want a URL field on library items so I can add a link to a full-text version.
* As a content editor, I need to add and edit partial dates for generic events so that I can record whatever portion of the date is available when the exact date is not known.
* As a user, I want to filter library members by birth year so that I can do generational comparison, such as looking at just members from the Lost Generation.
* Initial reactive Books search

0.17
----

* As a user, I want to filter library members by membership dates so that I can see who was active in the library in a particular time period.
* As a user, if I load the members search page with invalid input I want to see the error so I know what’s wrong and can tell when I’ve fixed the problem.

* bugfix: OCLC search syntax error breaks OCLC reconciliation
* updates templates for book & member details to use more semantic markup
* adds a stub book detail page

0.16
----

* As a user, I want to view and navigate by breadcrumbs so I know where I am in the site hierarchy and can navigate to pages above the one I'm on.
* As a content editor, I want to view and edit item format so I can designate item type.
* As a content editor, I want to view and edit item work URI, edition URI, and view subject and genre information so that I can review and correct the information.
* As an admin, I want items updated with matching OCLC work URI, best match edition URI, genre, and subjects so that I can include information from OCLC so users will know more about the books.

* bugfix: account earliest_date and last_date methods don't account for partially known dates
* bugfix: result list styles are broken on books list
* bugfix: tooltip is triggered by hovering space where it would appear

0.15
----

* As a user, I want the members list page updated as soon as I change search terms, filters, or results page so that I can refine my search without losing my place in the form and have results load more quickly.
* As a user, I want the count of members with cards to update as soon as I change search terms or filters so that I can see an accurate number for my current search.
* As a user, I want to filter library members by gender so that I can see the gender composition of library members.
* As a content editor, I want account id number listed in the person admin list view and person CSV export so that I have more information for decisions about merging people records.

* bugfix: don't defer loading of <script>s to avoid flash of unstyled content

0.14
----

* As a user I want members automatically sorted by relevance if I have a keyword search term active and otherwise by member name, so that I see best matches first for keyword searches.
* As a user, I want to filter library members to those with a lending card available on the site so that I can focus on members with cards and borrowing activity.
* As an admin, I want to see a report of OCLC work and edition URI matches for all items so that I can review and determine the criteria for acceptable matches.
* As a content editor, I want to add partial start and end date information for addresses so I can document the dates when only the month or year is known.

* Completes template and styles for pagination and sorting controls
* bugfix: members keyword search sort most relevant items first instead of last


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
