from django.template import TemplateSyntaxError
import pytest

from mep.accounts.templatetags.account_tags import as_ranges, group_consecutive


def test_group_consecutive():
    assert group_consecutive(["1919"]) == [(1919, 1919)]

    assert group_consecutive(["1919", "1920", "1921"]) == [(1919, 1921)]
    assert group_consecutive(["1919", "1921"]) == [(1919, 1919), (1921, 1921)]
    # sort if necessary
    assert group_consecutive(["1921", "1919"]) == [(1919, 1919), (1921, 1921)]
    # integer works too
    assert group_consecutive([1919]) == [(1919, 1919)]


def test_as_ranges():
    # single date
    assert as_ranges(["1919"]) == '<span class="date-range">1919</span>'
    # date span
    assert (
        as_ranges(["1919", "1920", "1921"])
        == '<span class="date-range">1919 – 1921</span>'
    )
    # multiple dates
    assert (
        as_ranges(["1919", "1920", "1930"])
        == '<span class="date-range">1919 – 1920</span> '
        + '<span class="date-range">1930</span>'
    )
    # error on non-integer
    with pytest.raises(TemplateSyntaxError):
        as_ranges(["nineteen"])
