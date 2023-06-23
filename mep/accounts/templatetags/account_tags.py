from itertools import groupby
from operator import itemgetter


from django.template import TemplateSyntaxError
from django.template.defaulttags import register
from django.utils.safestring import mark_safe


# group consecutive numbers solution from
# https://stackoverflow.com/questions/2154249/identify-groups-of-continuous-numbers-in-a-list
# based on python itertools examples


def group_consecutive(data):
    """turn a list of numbers into groups of consecutive ranges"""
    ranges = []
    # convert string to int
    try:
        data = [int(val) for val in data]
    except ValueError:
        raise TemplateSyntaxError("group_consecutive filter requires integers")

    data.sort()  # ensure values are sorted

    for k, g in groupby(enumerate(data), lambda x: x[0] - x[1]):
        group = map(itemgetter(1), g)
        group = list(map(int, group))
        ranges.append((group[0], group[-1]))

    return ranges


@register.filter
def as_ranges(years):
    """Display a set of years as a list of ranges"""

    # convert string to int
    try:
        data = [int(val) for val in years]
    except ValueError:
        raise TemplateSyntaxError("as_ranges filter requires numeric values")

    # group into tuples of ranges
    ranges = group_consecutive(data)
    # convert to string ranges; single year or range
    range_values = [
        str(start) if start == end else "%s – %s" % (start, end)
        for start, end in ranges
    ]
    # output as html
    result = " ".join(
        ['<span class="date-range">%s</span>' % dates for dates in range_values]
    )
    return mark_safe(result)
