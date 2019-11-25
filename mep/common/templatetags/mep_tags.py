import json
from urllib.parse import urlparse

from django.template.defaulttags import mark_safe, register
from django.template.defaultfilters import date
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
def ap_format(partial_date):
    '''Formats a partial date using the AP style for abbreviated month and
    showing only the available parts of the date, e.g. "Jan. 1934".'''
    # Return None if passed to preserve filter chaining
    if partial_date is None:
        return None

    # NOTE logic adapted from PartialDate.date_format

    # get the datetime and precision from the partial
    (dt, precision) = Event.partial_start_date.parse_date(str(partial_date))

    parts = []
    # Handle None as indicating full date precision
    if precision is None:
        parts = ['N ', 'j, ', 'Y']

    # cast integer to date precision to check flags
    precision = DatePrecision(precision)

    # If the date was not set, this value will be defaulted to no flags,
    # which is a boolean falsy, i.e. 0., so return no date.
    if not precision:
        return None

    # if values are missing, don't use them at all
    if precision.month:
        parts.append('N ')
    if precision.day and precision.year:
        parts.append('j, Y')
    elif precision.day:
        parts.append('j')
    elif precision.year:
        parts.append('Y')

    # format the date value using the generated string
    return date(dt, ''.join(parts))
