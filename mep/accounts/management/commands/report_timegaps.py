"""
Manage command to identify and report on large gaps in time between
events in a single library account, to identify possible candidates for
demerging.  Options allow specifying the minimum gap to look for in months
(default is 6 months) and a required filename to use for CSV output.
By default, borrowing events are not included.  If specified, borrowing
events will be included but borrow events with partially know dates
will be skipped.

Example usage::

    python manage.py report_timegaps -o 6month-gaps.csv
    python manage.py report_timegaps -g 12 months -o 12month-gaps.csv
    python manage.py report_timegaps -g 12 months --borrows -o 12month-gaps-with-borrows.csv


"""

import codecs
import csv
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db.models import Count

from mep.accounts.models import Account
from mep.common.utils import absolutize_url


class Command(BaseCommand):
    """Look for accounts with large time gaps between events to identify
    possible candidates for demerge"""

    help = __doc__

    #: default verbosity
    v_normal = 1
    verbosity = v_normal
    #: columns for CSV output
    csv_header = [
        "Admin URL(s)",
        "Account",
        "Account Date Range",
        "# Gaps",
        "Longest Gap in days",
        "Details",
    ]

    #: include borrowing events when checking for gaps between events?
    include_borrows = False

    def add_arguments(self, parser):
        parser.add_argument(
            "-g",
            "--gap",
            default=6,
            type=int,
            help="Minimum time gap in months. Default: %(default)d",
        )
        parser.add_argument(
            "-b",
            "--borrows",
            default=self.include_borrows,
            action="store_true",
            help="Include borrowing events when looking for gaps (excluded by default).",
        )
        parser.add_argument(
            "filename", help="Filename to use for generated CSV report."
        )

    def format_relativedelta(self, rel_delta):
        """Generate a human-readable display for a relativedelta in years,
        months, and days"""
        parts = []
        for attr in ["years", "months", "days"]:
            if getattr(rel_delta, attr):
                value = getattr(rel_delta, attr)
                # use attribute name for label, and strip off s if singular
                label = attr
                if value == 1:
                    label = attr.rstrip("s")
                parts.append("{} {}".format(value, label))

        return ", ".join(parts)

    def handle(self, *args, **kwargs):
        self.verbosity = kwargs["verbosity"]
        self.include_borrows = kwargs["borrows"]

        # find accounts with at least two events; order by id for now to avoid
        # issues with ordering on person sort name
        accounts = (
            Account.objects.annotate(num_events=Count("event"))
            .filter(num_events__gt=1)
            .order_by("id")
        )

        self.stdout.write(
            "Examining {} accounts with at least two events".format(accounts.count())
        )

        # generate a timedelta for comparison based on the configured
        # gap size to look for; assume 1 month = 30 days
        gap = timedelta(days=30 * kwargs["gap"])

        total = 0
        with open(kwargs["filename"], "w") as csvfile:
            # write utf-8 byte order mark at the beginning of the file
            csvfile.write(codecs.BOM_UTF8.decode())

            # initialize csv writer and write header row
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(self.csv_header)

            # loop through all accounts to find and report on time gaps
            for acct in accounts:
                # print summary info: account and full date range
                date_range = "{}/{}".format(acct.earliest_date(), acct.last_date())

                if self.verbosity > self.v_normal:
                    self.stdout.write("{} ({})".format(acct, date_range))

                # get a list of gaps (if any) for the current account
                gaps = self.find_gaps(acct, gap)

                # if any gaps were found, include the account in the report
                if gaps:
                    total += 1

                    max_gap, message = self.report_gap_details(gaps)
                    if self.verbosity > self.v_normal:
                        self.stdout.write(message)

                    # output account and date gap information to CSV report
                    admin_links = ";".join(
                        [
                            absolutize_url(pers.admin_url())
                            for pers in acct.persons.all()
                        ]
                    )
                    csvwriter.writerow(
                        [
                            admin_links,
                            str(acct),
                            date_range,
                            len(gaps),
                            max_gap,
                            message,
                        ]
                    )

        self.stdout.write(
            "Found {} accounts with gaps larger than {}".format(
                total, self.format_relativedelta(relativedelta(months=kwargs["gap"]))
            )
        )

    def find_gaps(self, account, gapsize):
        """Identify and return gaps between account events that are larger than the
        specified gap size. Returns a list of tuples of start and event dates
        for any gaps found.  Currently ignores borrow events with partially known
        dates.

        :param account: :class:`mep.accounts.models.Account`
        :param gapsize: :class:`datetime.timedelta`
        """

        gaps = []
        # set previous date and event to none for the first loop
        prev_date = None
        prev_event = None

        for evt in account.event_set.all():
            # skip borrow events with partially known dates
            if evt.event_type == "Borrow":
                # if include borrows not requested, skip
                if not self.include_borrows:
                    continue

                # if dates are set and are only partially known, skip
                # NOTE: might merit a method on the class to check if dates
                # are partially/fully known
                if (
                    evt.start_date
                    and evt.borrow.partial_start_date != evt.start_date.isoformat()
                    or evt.end_date
                    and evt.borrow.partial_end_date != evt.end_date.isoformat()
                ):
                    # report the skipped event in verbose mode
                    if self.verbosity > self.v_normal:
                        self.stdout.write(
                            "Skipping borrow event with partial dates {}".format(evt)
                        )

                    continue

            # if previous date is set, compare it with current event start
            if prev_date:
                # some borrow events in the database are currently
                # reporting no start date but an end date; use end date
                # if start date is not set
                # (and some borrows have no dates at all)
                compare_date = evt.start_date or evt.end_date

                # if current event is after the last one, then check gap
                # (i.e. ignore borrowing events during a subscription)
                if compare_date and compare_date > prev_date:
                    # generate timedelta for current event and the last one
                    delta = compare_date - prev_date
                    # if the delta is larger than our threshold, store the gap
                    if delta >= gapsize:
                        # store the two events so a relativedelta can
                        # be calculated and event types can be displayed
                        gaps.append((prev_event, evt))

            # store current event as previous event and previous date;
            # use end date if set, start date if not
            prev_date = evt.end_date or evt.start_date
            prev_event = evt

        return gaps

    def report_gap_details(self, gaps):
        """Given a list of gaps as generated by :meth:`find_gaps`,
        return the maximum gap size in days and a message reporting
        the specifics of the event types and dates with gaps."""
        details = []
        max_gap = 0
        for event1, event2 in gaps:
            # ideally, the gap should be calculated from the end of
            # the first event to the start of the next.
            # Use whichever date is present for each event.
            # - first event end if possible; fall back to start
            gap_start = event1.end_date or event1.start_date
            # - second event stat if possible; fall back to end
            gap_end = event2.start_date or event2.end_date
            rel_delta = relativedelta(gap_end, gap_start)
            # event2.start_date or event2.end_date,
            # event1.end_date or event1.start_date)
            # timedelt = event2.start_date - (event1.start_date or event1.end_date)
            timedelt = gap_end - gap_start
            max_gap = max(max_gap, timedelt.days)
            details.append(
                "{} between {} {} and {} {}".format(
                    self.format_relativedelta(rel_delta),
                    event1.date_range,
                    event1.event_type,
                    event2.date_range,
                    event2.event_type,
                )
            )

        return max_gap, "; ".join(details)
