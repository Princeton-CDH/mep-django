import datetime

from django.core.validators import ValidationError
from django.db import models
from django.test import TestCase
import pytest

from mep.accounts.models import Account, Borrow
from mep.accounts.partial_date import DatePrecision, DatePrecisionField, \
    PartialDate, PartialDateMixin


class TestPartialDateField(TestCase):

    def test_to_python(self):
        dpf = DatePrecisionField()
        # cast value to date precision
        assert isinstance(dpf.to_python(1), DatePrecision)
        # handle None
        assert dpf.to_python(None) is None

    def test_from_db_value(self):
        dpf = DatePrecisionField()
        # cast value to date precision
        assert isinstance(dpf.from_db_value(1, None, None, None),
                          DatePrecision)
        # handle None
        assert dpf.from_db_value(None, None, None, None) is None


class TestPartialDate(TestCase):

    # test object for partial date descriptor behavior
    class PartialDateObject(models.Model):
        date = None
        partial_date = PartialDate('date', 'date_precision')
        date_precision = DatePrecisionField()

        class Meta:
            abstract = True

    # version that uses 1900 for unknown years
    class PartialDateObject1900(PartialDateObject):
        partial_date = PartialDate('date', 'date_precision', 1900)

        class Meta:
            abstract = True

    def test_get(self):
        pdo = self.PartialDateObject()
        # should not error if date is not set
        assert pdo.partial_date is None
        # full precision
        pdo.date = datetime.date(1901, 3, 5)
        pdo.date_precision = DatePrecision.year | DatePrecision.month | DatePrecision.day
        assert pdo.partial_date == '1901-03-05'
        # NULL date precision returns full year
        pdo.date_precision = None
        assert pdo.partial_date == '1901-03-05'
        # partial precision
        pdo.date_precision = DatePrecision.year | DatePrecision.month
        assert pdo.partial_date == '1901-03'
        pdo.date_precision = DatePrecision.month | DatePrecision.day
        assert pdo.partial_date == '--03-05'
        pdo.date_precision = DatePrecision.year
        assert pdo.partial_date == '1901'

        # change default unknown year value
        pdo = self.PartialDateObject1900()
        pdo.date = datetime.date(1900, 3, 5)
        pdo.date_precision = DatePrecision.month | DatePrecision.day
        assert pdo.partial_date == '--03-05'

        # get with no object should return the descriptor for documentation
        # purposes
        assert isinstance(self.PartialDateObject.partial_date, PartialDate)

    def test_set(self):
        pdo = self.PartialDateObject()
        # sets date and date precision
        pdo.partial_date = '1901-03-05'
        assert pdo.date == datetime.date(1901, 3, 5)
        assert pdo.date_precision == DatePrecision.year | DatePrecision.month | DatePrecision.day
        # partial precision
        pdo.partial_date = '--03-05'
        assert pdo.date == datetime.date(1, 3, 5)
        assert pdo.date_precision == DatePrecision.month | DatePrecision.day

        # errors on invalid dates
        with pytest.raises(ValidationError):
            pdo.partial_date = '05'
        with pytest.raises(ValidationError):
            pdo.partial_date = 'definitely_not_a_date'

        # should clear the values if None is passed
        pdo.partial_date = None
        assert pdo.date is None
        assert pdo.date_precision is None

        # change default unknown year value
        pdo = self.PartialDateObject1900()
        pdo.partial_date = '--03-05'
        assert pdo.date == datetime.date(1900, 3, 5)
        assert pdo.date_precision == DatePrecision.month | DatePrecision.day

    def test_parse_date(self):
        partial_date = self.PartialDateObject.partial_date
        assert partial_date.parse_date('1901-03-05') == \
            (datetime.date(1901, 3, 5), DatePrecision.year | DatePrecision.month | DatePrecision.day)
        assert partial_date.parse_date('1901-03') == \
            (datetime.date(1901, 3, 1), DatePrecision.year | DatePrecision.month)
        assert partial_date.parse_date('1901') ==  \
            (datetime.date(1901, 1, 1), DatePrecision.year)

        # invalid partial precision
        with pytest.raises(ValidationError):
            partial_date.parse_date('05')
        with pytest.raises(ValidationError):
            partial_date.parse_date('1901--05')
        with pytest.raises(ValidationError):
            partial_date.parse_date('no date')
        with pytest.raises(ValidationError):
            # month with unknown year
            partial_date.parse_date('--05')


class TestPartialDateMixin(TestCase):

    class PartialMixinObject(PartialDateMixin):

        class Meta:
            abstract = True

    def test_calculate_date(self):

        pmo = self.PartialMixinObject()
        with pytest.raises(ValueError):
            # unsupported date name should error
            pmo.calculate_date('bogus')

        # partial date
        pmo.calculate_date('start_date', '1935-05')
        assert pmo.start_date == datetime.date(1935, 5, 1)
        assert pmo.start_date_precision.year
        assert pmo.start_date_precision.month
        assert not pmo.start_date_precision.day

        # 1900 date = unknown by project convention
        pmo.calculate_date('end_date', '1901-06-30')
        assert pmo.end_date == datetime.date(1901, 6, 30)
        assert not pmo.end_date_precision.year
        assert pmo.end_date_precision.month
        assert pmo.end_date_precision.day

        # earliest/latest dates
        early = datetime.date(1930, 11, 5)
        late = datetime.date(1930, 11, 25)
        pmo.calculate_date('start_date', earliest=early, latest=late)
        # stored as earliest date
        assert pmo.start_date == early
        assert pmo.partial_start_date == '1930-11'
        # in this case, all but day match
        assert pmo.start_date_precision.year
        assert pmo.start_date_precision.month
        assert not pmo.start_date_precision.day

        # only year overlaps
        late = datetime.date(1930, 12, 25)
        pmo.calculate_date('start_date', earliest=early, latest=late)
        assert pmo.partial_start_date == '1930'
        assert pmo.start_date_precision.year
        assert not pmo.start_date_precision.month

        # different year but same month/day
        late = datetime.date(1932, 11, 5)
        pmo.calculate_date('start_date', earliest=early, latest=late)
        assert pmo.start_date == early
        assert pmo.partial_start_date == '--11-05'
        assert not pmo.start_date_precision.year
        assert pmo.start_date_precision.month
        assert pmo.start_date_precision.day

        # no overlap?
        late = datetime.date(1932, 12, 22)
        pmo.calculate_date('start_date', earliest=early, latest=late)
        assert not pmo.partial_start_date
        assert not pmo.start_date_precision

    def test_date_range(self):

        # test both dates being the same returning date in partial date format
        pmo = self.PartialMixinObject()
        pmo.calculate_date('start_date', '1930-01-01')
        pmo.calculate_date('end_date', '1930-01-01')
        assert pmo.date_range == '1930-01-01'

        # test that two dates produce / joined dates
        pmo.calculate_date('end_date', '1930-01-02')
        assert pmo.date_range == '1930-01-01/1930-01-02'

        # test that an unknown date is rendered as ??
        pmo.end_date = None
        pmo.calculate_date('end_date')
        assert pmo.date_range == '1930-01-01/??'


@pytest.mark.django_db
def test_knownyear_filter():
    # create borrow event to test
    acct = Account.objects.create()
    borrow = Borrow(account=acct, end_date=datetime.date(1950, 2, 12))
    # fully known date
    borrow.partial_start_date = '1940-01-01'
    borrow.save()
    # known year = true should return 1 borrow
    assert Borrow.objects.filter(start_date_precision__knownyear=True).exists()
    # known year = false should not find anything
    assert not Borrow.objects.filter(start_date_precision__knownyear=False).exists()

    # partially known date with year should work the same
    borrow.partial_start_date = '1940-01'
    borrow.save()
    # known year = true should return 1 borrow
    assert Borrow.objects.filter(start_date_precision__knownyear=True).exists()
    # known year = false should not find anything
    assert not Borrow.objects.filter(start_date_precision__knownyear=False).exists()

    # year unknown
    borrow.partial_start_date = '--01-01'
    borrow.save()
    # known year = true should not find anything
    assert not Borrow.objects.filter(start_date_precision__knownyear=True).exists()
    # known year = false should return 1 borrow
    assert Borrow.objects.filter(start_date_precision__knownyear=False).exists()

    # test end - date set directly, not through partial date descriptor
    # known year = true should return 1 borrow
    assert Borrow.objects.filter(end_date_precision__knownyear=True).exists()
    # known year = false should not find anything
    assert not Borrow.objects.filter(end_date_precision__knownyear=False).exists()
