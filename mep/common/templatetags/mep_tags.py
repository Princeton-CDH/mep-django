import json
import string
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import date
from django.template.defaulttags import mark_safe, register
from piffle.iiif import IIIFImageClientException

from mep.accounts.models import Event
from mep.accounts.partial_date import DatePrecision


@register.filter
def dict_item(dictionary, key):
    ''''Template filter to allow accessing dictionary value by variable key.
    Example use::

        {{ mydict|dict_item:keyvar }}
    '''
    return dictionary.get(key, None)


@register.filter(name='json')
def json_dumps(data):
    return mark_safe(json.dumps(data))


@register.filter
def domain(url):
    '''Template filter to extract the domain part of a link, for use in creating
    link text automatically from a URL. Example use::

        <a href="{{ url }}">{{ url|domain }}</a>

    which could create something like::

        <a href="http://en.wikipedia.org/">wikipedia</a>

    Note that this doesn't work on URLs without a // in them, following syntax
    specified in RFC 1808 as implemented in Python's `urlparse`.
    '''
    try:
        netloc_parts = urlparse(url).netloc.split('.')
        return netloc_parts[-2]  # piece right before the top-level domain
    except (TypeError, IndexError, ValueError, AttributeError):
        return None


@register.filter
def iiif_image(img, args):
    '''Add options to resize or otherwise change the display of an iiif
    image; expects an instance of :class:`piffle.iiif.IIIFImageClient`.
    Provide the method and arguments as filter string, i.e.::

        {{ myimg|iiif_image:"size:width=225,height=255" }}
    '''
    # split into method and parameters (return if not formatted properly)
    if ':' not in args:
        return ''
    mode, opts = args.split(':')
    # split parameters into args and kwargs
    args = opts.split(',')
    # if there's an =, split it and include in kwargs dict
    kwargs = dict(arg.split('=', 1) for arg in args if '=' in arg)
    # otherwise, include as an arg
    args = [arg for arg in args if '=' not in arg]
    # attempt to call the method with the arguments
    try:
        return getattr(img, mode)(*args, **kwargs)
    except (IIIFImageClientException, TypeError):
        # return an empty string if anything goes wrong
        return ''


@register.filter
def partialdate(val, date_format=None):
    '''Template filter analogous to Django's
    :meth:`django.template.defaultfilters.date` but for
    :class:`mep.accounts.partial_date.PartialDate`.
    Takes a partial date value (string representation, e.g. 1934-01 or
    --11-26), parses it, and filters out any values in the format string
    that are not known based on date precision.  Note: may not handle all
    cases where punctuation is left stranded by a removed portion of
    the date.'''

    # Return None if passed to preserve filter chaining
    if val is None:
        return

    # use default date format if none is specified, same as django
    if date_format is None:
        date_format = settings.DATE_FORMAT

    # use translation tables to remove date format characters based
    # on available precision
    # based on groupings in Django documentation:
    # https://docs.djangoproject.com/en/2.2/ref/templates/builtins/#date
    # Currently ignores time and date/time formats.
    day_formats = str.maketrans('', '', 'djDlSwz')
    month_formats = str.maketrans('', '', 'mnMbEFNt')
    year_formats = str.maketrans('', '', 'yYLo')
    week_formats = str.maketrans('', '', 'W')
    # NOTE: might be better to use regex replacement
    # in order to remove any punctuation attached to a format string
    # that isn't supported by the precision, but translate is faster

    # parse partial date back into datetime and precision
    try:
        (dt, precision) = Event.partial_start_date.parse_date(str(val))
    except ValidationError:
        # bail out if date couldn't be parsed
        return

    # cast integer to date precision to check flags
    precision = DatePrecision(precision)

    # remove any format strings that we don't have precision for
    # - precision None means full precision
    if precision is not None:
        if not precision.day:
            date_format = date_format.translate(day_formats)
        if not precision.month:
            date_format = date_format.translate(month_formats)
        if not precision.year:
            date_format = date_format.translate(year_formats)
        # day + month + year required to calculate week
        if not all([precision.day, precision.month, precision.year]):
            date_format = date_format.translate(week_formats)

        # remove any stranded commas (not sure how to generalize punctuation)
        # and any trailing whitespace + punctuation
        date_format = date_format.replace(' , ', ' ') \
            .strip(''.join([string.punctuation, string.whitespace])) \

    # if everything has been removed, don't generate a date because
    # we'll get django default format
    if not date_format:
        return

    # format the date value using the django's date templatetag and
    # the revised format string
    return date(dt, date_format)
