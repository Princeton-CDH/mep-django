from urllib.parse import urlparse

from django.template.defaulttags import register


@register.filter
def dict_item(dictionary, key):
    ''''Template filter to allow accessing dictionary value by variable key.
    Example use::

        {{ mydict|dict_item:keyvar }}
    '''
    return dictionary.get(key, None)

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
        return netloc_parts[-2] # piece right before the top-level domain
    except (IndexError, ValueError): # parser fail or no domain portion
        return None
