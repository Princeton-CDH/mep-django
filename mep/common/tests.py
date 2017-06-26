import pytest
import re

from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import AliasIntegerField, Named, Notable, DateRange


class TestNamed(TestCase):

    def test_repr(self):
        named_obj = Named(name='foo')
        overall = re.compile(r'<Named \{.+\}>')
        assert re.search(overall, repr(named_obj))

    def test_str(self):
        named_obj = Named(name='foo')
        assert str(named_obj) == 'foo'


class TestNotable(TestCase):

    def test_has_notes(self):
        noted = Notable()
        assert False == noted.has_notes()
        noted.notes = 'some text'
        assert True == noted.has_notes()
        noted.notes = ''
        assert False == noted.has_notes()
        noted.notes = None
        assert False == noted.has_notes()

class TestDateRange(TestCase):

    def test_dates(self):
        span = DateRange()
        # no dates set
        assert '' == span.dates
        # date range with start and end
        span.start_year = 1900
        span.end_year = 1901
        assert '1900-1901' == span.dates
        # start and end dates are same year = single year
        span.end_year = span.start_year
        assert span.start_year == span.dates
        # start date but no end
        span.end_year = None
        assert '1900-' == span.dates
        # end date but no start
        span.end_year = 1950
        span.start_year = None
        assert '-1950' == span.dates

    def test_clean_fields(self):
        with pytest.raises(ValidationError):
            DateRange(start_year=1901, end_year=1900).clean_fields()

        # should not raise exception
        # - same year is ok (single year range)
        DateRange(start_year=1901, end_year=1901).clean_fields()
        # - end after start
        DateRange(start_year=1901, end_year=1905).clean_fields()
        # - only one date set
        DateRange(start_year=1901).clean_fields()
        DateRange(end_year=1901).clean_fields()
        # exclude set
        DateRange(start_year=1901, end_year=1900).clean_fields(exclude=['start_year'])
        DateRange(start_year=1901, end_year=1900).clean_fields(exclude=['end_year'])


class TestAliasIntegerField(TestCase):

    def setUp(self):
        class TestModel(DateRange):
            foo_year = AliasIntegerField(db_column='start_year')
            bar_year = AliasIntegerField(db_column='end_year')
        self.TestModel = TestModel

    def test_aliasing(self):
        TestModel = self.TestModel
        # Should pass the exact same tests as date range with the new fields
        with pytest.raises(ValidationError):
            TestModel(foo_year=1901, bar_year=1900).clean_fields()

        # should not raise exception
        # - same year is ok (single year range)
        TestModel(foo_year=1901, bar_year=1901).clean_fields()
        # - end after start
        TestModel(foo_year=1901, bar_year=1905).clean_fields()
        # - only one date set
        TestModel(foo_year=1901).clean_fields()
        TestModel(bar_year=1901).clean_fields()
        # exclude set (still using old attributes in exclude since we're just
        # linking here)
        TestModel(
            foo_year=1901,
            bar_year=1900
        ).clean_fields(exclude=['start_year'])
        TestModel(
            foo_year=1901,
            bar_year=1900
        ).clean_fields(exclude=['end_year'])

    def test_error_on_create_non_field(self):
        with pytest.raises(AttributeError) as e:
            # simulate passing a None because the object didn't set right
            AliasIntegerField.__get__(AliasIntegerField(), None)
        assert ('Are you trying to set a field that does not '
                'exist on the aliased model?') in str(e)
