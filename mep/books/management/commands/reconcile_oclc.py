import codecs
from collections import defaultdict
import csv

from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
import progressbar
import pymarc

from mep.books.models import Work
from mep.books.oclc import SRUSearch


class Command(BaseCommand):
    """Associate library items with OCLC entries via WorldCat Search API"""

    help = __doc__

    mode = None
    sru_search = None

    #: fields to be included in CSV export
    csv_fieldnames = [
        # details from local db
        "Title",
        "Date",
        "Creators",
        # details from OCLC
        "OCLC Title",
        "OCLC Author",
        "OCLC Date",
        "OCLC URI",
        "Work URI",
        "# matches",
        # db notes last
        "Notes",
    ]

    #: summary message string for each mode
    summary_message = {
        "report": "Processed %(count)d works, found matches for %(found)d",
        "update": "Processed %(count)d works, updated %(updated)d, no matches for %(no_match)d, %(error)d error(s)",
    }

    progbar = None

    #: notes indicator for reconciliation attempted but no match found
    oclc_no_match = "OCLCNoMatch"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = defaultdict(int)

        self.script_user = User.objects.get(username=settings.SCRIPT_USERNAME)
        self.work_content_type = ContentType.objects.get_for_model(Work).pk

    def add_arguments(self, parser):
        parser.add_argument("mode", choices=["report", "update"])
        parser.add_argument(
            "--no-progress", action="store_true", help="Do not display progress bar"
        )
        parser.add_argument(
            "-o", "--output", help="Filename for the report to be generated"
        )

    def handle(self, *args, **kwargs):
        """Loop through Works in the database and look for matches in OCLC"""

        # store operating mode
        self.mode = kwargs["mode"]
        # initialize OCLC search client
        self.sru_search = SRUSearch()

        # filter out works with problems that we don't expect to be
        # able to match reliably
        # only include works that do not already have a work URI
        works = (
            Work.objects.exclude(notes__contains="GENERIC")
            .exclude(notes__contains="PROBLEM")
            .exclude(notes__contains="OBSCURE")
            .exclude(notes__contains="ZERO")
            .exclude(notes__contains=self.oclc_no_match)
            .filter(uri__exact="")
            .exclude(title__endswith="*")
        )

        # report on total to process
        total = works.count()
        self.stdout.write("%d works to reconcile" % total)

        # bail out if there is nothing to do
        if not total:
            return

        if not kwargs["no_progress"] and total > 5:
            self.progbar = progressbar.ProgressBar(
                redirect_stdout=True, max_value=total
            )
        if self.mode == "report":
            # use output name specified in args, with a default fallback
            outfilename = kwargs.get("output", None) or "works-oclc.csv"
            self.report(works, outfilename)
        elif self.mode == "update":
            self.update_works(works)

        if self.progbar:
            self.progbar.finish()

        # summarize what was done for the current mode
        self.stdout.write(self.summary_message[self.mode] % self.stats)

    def tick(self):
        """Increase count by one and update progress bar if there is one"""
        self.stats["count"] += 1
        if self.progbar:
            self.progbar.update(self.stats["count"])

    def report(self, works, outfilename):
        """Generate an CSV file to report on OCLC matches found"""
        with open(outfilename, "w") as csvfile:
            # write utf-8 byte order mark at the beginning of the file
            csvfile.write(codecs.BOM_UTF8.decode())
            # initialize csv writer
            writer = csv.DictWriter(csvfile, fieldnames=self.csv_fieldnames)
            writer.writeheader()

            for work in works:
                info = {
                    "Title": work.title,
                    "Date": work.year,
                    "Creators": ";".join(
                        [str(person) for person in work.creators.all()]
                    ),
                    "Notes": work.notes,
                }
                info.update(self.oclc_info(work))
                writer.writerow(info)
                # keep track of how many records found any matches
                if info.get("# matches", None):
                    self.stats["found"] += 1

                self.tick()

    def update_works(self, works):
        """Search for Works in OCLC and update in the database if
        a match is found."""
        for work in works:
            error = False
            log_message = None

            try:
                worldcat_entity = self.oclc_search_record(work)
            except ConnectionError as err:
                self.stderr.write("Error: %s" % err)
                worldcat_entity = None
                self.stats["error"] += 1
                error = True

            if worldcat_entity:
                work.populate_from_worldcat(worldcat_entity)
                work.save()
                # message for log entry to document the change
                log_message = "Updated from OCLC %s" % worldcat_entity.work_uri
                self.stats["updated"] += 1

            # if no match was found but there was no connection error,
            # make a note and log the change
            elif not error:
                # add no match indicator to work notes
                work.notes = "\n".join(
                    [txt for txt in (work.notes, self.oclc_no_match) if txt]
                )
                work.save()
                # message for log entry to document the change
                log_message = "No OCLC match found"
                self.stats["no_match"] += 1

            # create a log entry if a message was set
            # (either updateor no match found)
            if log_message:
                LogEntry.objects.log_action(
                    user_id=self.script_user.id,
                    content_type_id=self.work_content_type,
                    object_id=work.pk,
                    object_repr=str(work),
                    change_message=log_message,
                    action_flag=CHANGE,
                )

            self.tick()

    def oclc_search(self, work):
        """Search for an work in OCLC by title, author, date, and
        material type if noted as a Periodical.  Filters by
        english language and material type not Internet Resource
        (i.e. electronic edition). Returns :class:`~mep.books.oclc.SRWResponse`.
        """
        search_opts = {}

        # search by title if known
        if work.title:
            search_opts["title__exact"] = work.title

        # search by first author if there is one
        if work.authors:
            search_opts["author__all"] = str(work.authors[0])

        # search by year if known
        if work.year:
            search_opts["year"] = work.year
        # search year by range based on first documented event for this book
        else:
            first_date = work.first_known_interaction
            if first_date:
                # range search ending with first known event date
                search_opts["year"] = "-%s" % first_date.year

        # filter by material type; assume work is a book unless
        # notes indicate periodical
        search_opts["material_type__exact"] = (
            "periodical" if "PERIODICAL" in work.notes else "book"
        )

        # add filters that apply to all S&co content
        # restrict to english language content
        # (nearly all are english, handful that are not will be handled manually)
        search_opts["language_code__exact"] = "eng"
        # exclude electronic books
        search_opts["material_type__notexact"] = "Internet Resource"

        return self.sru_search.search(**search_opts)

    def oclc_info(self, work):
        """Search for an work in OCLC by title, author, date.
        Returns dictionary with details found for inclusion in CSV.
        """
        result = self.oclc_search(work)
        # report number of matches so 0 is explicit/obvious
        oclc_info = {"# matches": result.num_records}
        if result.num_records:
            # assume first record is best match (seems to be true)
            marc_record = result.marc_records[0]
            try:
                worldcat_rdf = self.sru_search.get_worldcat_rdf(marc_record)
                oclc_info.update(
                    {
                        "OCLC Title": marc_record.title(),
                        "OCLC Author": marc_record.author(),
                        "OCLC Date": marc_record.pubyear(),
                        "OCLC URI": worldcat_rdf.work_uri,
                        "Work URI": worldcat_rdf.work_uri,
                    }
                )
            except ConnectionError as err:
                self.stderr.write("Error: %s" % err)

        return oclc_info

    def oclc_search_record(self, work):
        """Search for an work in OCLC by title, author, date.
        Returns :class:`~mep.books.oclc.WorldCatResource` for the first
        match.'''
        """
        result = self.oclc_search(work)
        if result and result.num_records:
            return self.sru_search.get_worldcat_rdf(result.marc_records[0])
