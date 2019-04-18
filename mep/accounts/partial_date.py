import re
import datetime

from django.db import models
from django.core.validators import ValidationError
from flags import Flags


class DatePrecision(Flags):
    '''Flag class to indicate which parts of a date are known.'''
    year = ()
    month = ()
    day = ()


class DatePrecisionField(models.PositiveSmallIntegerField):
    '''Integer representation of a :class:`DatePrecision`.'''
    description = 'Integer representation of DatePrecision flags.'

    def to_python(self, value):
        return DatePrecision(value) if value else None


class PartialDate:
    '''Descriptor that gets and sets a related :class:`datetime.date` and
    :class:`DatePrecision` from partial date strings, e.g. --05-02.'''

    description = 'Partial date generated from date and date precision flags'

    partial_date_re = re.compile(
        r'^(?P<year>\d{4}|-)?(?:-(?P<month>[01]\d))?(?:-(?P<day>[0-3]\d))?$'
    )

    def __init__(self, date_field, date_precision_field, unknown_year:int=1,
                 label=None):
        self.date_field = date_field
        self.date_precision_field = date_precision_field
        self.unknown_year = unknown_year

        # set attributes for display/sort in django admin
        self.admin_order_field = date_field
        if label:
            self.short_description = label

    def __get__(self, obj, objtype=None):
        '''Use :meth:`date_format` to transform a  :class:`datetime.date` and
        :class:`DatePrecision` to a partial date string. If the date doesn't
        exist yet, return None.'''
        if obj is None:
            return self
        date_val = getattr(obj, self.date_field, None)
        if date_val:
            date_precision_val = getattr(obj, self.date_precision_field)
            return date_val.strftime(self.date_format(date_precision_val))

    def __set__(self, obj, val):
        '''Call :meth:`parse_date` to parse a partial date and set the
        :class:`datetime.date` and :class:`DatePrecision`. If a falsy value was
        passed, set them both to None.'''
        (date_val, date_precision_val) = self.parse_date(val) if val else (None, None)
        setattr(obj, self.date_field, date_val)
        setattr(obj, self.date_precision_field, date_precision_val)

    @staticmethod
    def date_format(value):
        '''Return a format string for use with :meth:`datetime.date.strftime`
        to output a date with the appropriate precision'''
        parts = []
        # cast integer to date precision to check flags
        value = DatePrecision(value)

        # no precision = no date
        if not value:
            return ''

        if value.year:
            parts.append('%Y')
        else:
            # if no year, indicate with --
            parts.append('-')
        if value.month:
            parts.append('%m')
        if value.day:
            parts.append('%d')

        # this is potentially ambiguous in some cases, but those cases
        # may not be meaningful anyway
        return '-'.join(parts)

    def parse_date(self, value):
        '''Parse a partial date string and return a :class:`datetime.date`
        and precision value.'''
        # partial date parsing adapted in part from django_partial_date
        # https://github.com/ktowen/django_partial_date
        match = self.partial_date_re.match(value)
        if match:
            match_info = match.groupdict()

            # turn matched values into numbers for initializing date object
            date_values = {}
            date_parts = []
            for k, v in match_info.items():
                try:
                    date_values[k] = int(v)
                    date_parts.append(k)
                except (TypeError, ValueError): # value was None or '-'
                    date_values[k] = self.unknown_year if k == 'year' else 1

            if date_parts == ['day'] or date_parts == ['month'] or date_parts == ['year', 'day']:
                raise ValidationError('"%s" is not a recognized date.''' % value)

            # determine known date parts based on regex match values
            # and initialize pecision flags accordingly
            precision = DatePrecision.from_simple_str('|'.join(date_parts))
            return (datetime.date(**date_values), precision)

        else:
            raise ValidationError('"%s" is not a recognized date.''' % value)


class PartialDateMixin(models.Model):
    '''Mixin to add fields for partial start and end dates to a model using
    :class:`DatePrecisionField` and :class:`PartialDate`.'''
    UNKNOWN_YEAR = 1900

    start_date_precision = DatePrecisionField(null=True, blank=True)
    end_date_precision = DatePrecisionField(null=True, blank=True)
    partial_start_date = PartialDate(
        'start_date', 'start_date_precision', UNKNOWN_YEAR, label='start date')
    partial_end_date = PartialDate(
        'end_date', 'end_date_precision', UNKNOWN_YEAR, label='end date')

    class Meta:
        abstract = True

    def calculate_date(self, kind, dateval=None, earliest=None, latest=None):
        '''Calculate end or start date based on a single value in a
        supported partial date form or based on earliest/latest datetime.'''

        # kind must be either start_date or end_date
        if kind not in ['start_date', 'end_date']:
            raise ValueError

        # if there is a single date value, use partial date to parse it
        # and set date precision
        if dateval:
            setattr(self, 'partial_%s' % kind, dateval)
            # special case:
            # 1900 dates were used to indicate unknown year; book store didn't
            # open until 1919, so any year before that should be marked unknown
            if getattr(self, kind).year < 1919:
                setattr(self, '%s_precision' % kind,
                        DatePrecision.month | DatePrecision.day)

        # no exact date, but earliest/latest possible dates
        elif earliest and latest:
            # store earliest datetime
            setattr(self, kind, earliest)
            precision = DatePrecision()
            # calculate the precision based on values in common
            if earliest.year == latest.year:
                precision |= DatePrecision.year
            if earliest.month == latest.month:
                precision |= DatePrecision.month
            if earliest.day == latest.day:
                precision |= DatePrecision.day

            # store the precision
            setattr(self, '%s_precision' % kind, precision)

    @property
    def date_range(self):
        '''Borrowing event date range as string, using partial dates.
        Returns a single date in partial date format if both dates are
        set to the same date. Uses "??" for unset dates,
        and returns in format start/end.'''

        # NOTE: this is the same logic as the Event date range method,
        # just substituting partial start and end dates and dropping the
        # isoformat method call.

        # if both dates are set and the same, return a single date
        if self.partial_start_date and self.partial_end_date and \
                self.partial_start_date == self.partial_end_date:
            return self.partial_start_date

        # otherwise, use both dates with ?? to indicate unknown date
        return '/'.join([dt if dt else '??'
                         for dt in [self.partial_start_date,
                                    self.partial_end_date]])


@models.Field.register_lookup
class KnownYear(models.Lookup):
    '''Custom lookup to filter on known year in `:class:`DatePrecisionField`'''
    lookup_name = 'knownyear'
    prepare_rhs = False

    def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)

        bit_compare = "%s & %d" % (lhs, int(DatePrecision.year))
        # if true (year is known), precision should be null or year bit set
        if self.rhs:
            return "%s IS NULL OR %s != 0" % (lhs, bit_compare), params

        # for false (year is unknown), bit should not be set
        return "%s = 0" % bit_compare, params
