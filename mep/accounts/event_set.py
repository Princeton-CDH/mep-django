import datetime
from itertools import chain

from django.db.models.functions import Coalesce


class EventSetMixin:
    '''Mixin with logic for aggregating events. Originally developed for use
    with :class:`~mep.accounts.models.Account`, but pulled out as a mixin
    for use with :class:`~mep.books.models.Book`. Should only be used
    with Models that have an `event_set`.
    '''

    @property
    def event_dates(self):
        '''sorted list of all unique event dates associated with this
        account or book; ignores borrow and purchase dates with unknown year'''
        # get value list of all start and end dates
        date_values = self.event_set.known_years() \
            .values_list('start_date', 'end_date')
        # flatten list of tuples into a list, filter out None, and make unique
        uniq_dates = set(filter(None, chain.from_iterable(date_values)))
        # return as a sorted list
        return sorted(list(uniq_dates))

    @property
    def event_years(self):
        '''list of unique years, based on :attr:`event_dates`'''
        return list(set(d.year for d in self.event_dates))

    def event_date_ranges(self, event_type=None):
        '''Generate and return a list of date ranges this account/book
        was active, based on associated events. Optionally filter
        to a specific kind of event activity (currently only
        supports membership).
        '''
        ranges = []
        current_range = None

        events = self.event_set.known_years() \
                               .annotate(
            first_date=Coalesce('start_date', 'end_date')
        ).order_by('first_date')

        # if event type was specified, filter as requested
        if event_type == 'membership':
            events = events.membership_activities()

        for event in events:
            # if no date is set, ignore
            if not event.start_date and not event.end_date:
                continue

            # if either date is partial with month unknown, skip
            if (event.start_date and event.start_date_precision and
               not event.start_date_precision.month) or \
               (event.end_date and event.end_date_precision and
               not event.end_date_precision.month):
                continue

            # if only one date is known, use for start/end of
            # range (i.e., borrow event with no end date)
            if not event.start_date or not event.end_date:
                date = event.start_date or event.end_date
                start_date = end_date = date

            # otherwise, use start and end dates for range
            else:
                start_date = event.start_date
                end_date = event.end_date

            # if no current range is set, create one from current event
            if not current_range:
                current_range = [start_date, end_date]
            # if this event starts within the current range, include it
            # NOTE: includes the following day; if this event is the
            # next day after the current range, extend the same range
            elif current_range[0] <= start_date <= \
                    (current_range[1] + datetime.timedelta(days=1)):
                current_range[1] = max(end_date, current_range[1])
            # otherwise, close out the current range and start a new one
            else:
                ranges.append(current_range)
                current_range = [start_date, end_date]

        # store the last range after the loop ends
        if current_range:
            ranges.append(current_range)
        return ranges

    def active_months(self, event_type=None):
        '''Generate and return a list of year/month dates this account/book
        was active, based on associated events. Optionally filter
        to a specific kind of event activity (currently supports
        "membership" or "books").
        Months are returned as a set in YYYYMM format.
        '''
        months = set()

        # Book activities are handled differently, since they do not
        # span multiple months; no need to convert to date ranges
        if event_type == 'books':
            book_events = self.event_set.known_years().book_activities()
            for event in book_events:
                # skip unset dates and unknown months (precision unset
                # or month flag present); add all other
                # to the set of years & months in YYYYMM format
                if event.start_date and \
                   (not event.start_date_precision or
                        event.start_date_precision.month):
                    months.add(event.start_date.strftime('%Y%m'))
                if event.end_date and \
                   (not event.end_date_precision or
                        event.end_date_precision.month):
                    months.add(event.end_date.strftime('%Y%m'))

            return months

        # For general events or membership activity,
        # calculate months based on date ranges to track months
        # when a subscription was active
        date_ranges = self.event_date_ranges(event_type)
        for start_date, end_date in date_ranges:
            current_date = start_date
            while current_date <= end_date:
                # if date is within range,
                # add to set of months in YYYYMM format
                months.add(current_date.strftime('%Y%m'))
                # get the date for the first of the next month
                next_month = current_date.month + 1
                year = current_date.year
                # handle december to january
                if next_month == 13:
                    year += 1
                    next_month = 1
                current_date = datetime.date(year, next_month, 1)
        return months

    def earliest_date(self):
        '''Earliest known date from all events associated with this account/book'''
        dates = self.event_dates
        if dates:
            return dates[0]

    def last_date(self):
        '''Last known date from all events associated with this account/book'''
        dates = self.event_dates
        if dates:
            return dates[-1]
