import pytest
import re
from unittest.mock import Mock

from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import AliasIntegerField, Named, Notable, DateRange
from .validators import verify_latlon
from .admin import LocalUserAdmin


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

    def test_note_snippet(self):
        noted = Notable()
        assert noted.note_snippet() == ''

        noted.notes = 'short note'
        assert noted.note_snippet() == noted.notes

        noted.notes = 'a very long note that goes on and on and and on and on and keeps going blah blah so it needs truncation'
        snip = noted.note_snippet()
        assert snip != noted.notes
        assert snip.endswith(' ...')
        assert snip.startswith(noted.notes[:75])


class TestDateRange(TestCase):

    def test_dates(self):
        span = DateRange()
        # no dates set
        assert span.dates == ''
        # date range with start and end
        span.start_year = 1900
        span.end_year = 1901
        assert '1900-1901' == span.dates
        # start and end dates are same year = single year
        span.end_year = span.start_year
        assert span.dates == str(span.start_year)
        # start date but no end
        span.end_year = None
        assert span.dates == '1900-'
        # end date but no start
        span.end_year = 1950
        span.start_year = None
        assert span.dates == '-1950'
        # negative start date but no end
        span.start_year = -150
        span.end_year = None
        assert span.dates == '150 BCE-'
        # negative end date but no start
        span.start_year = None
        span.end_year = -201
        assert span.dates == '-201 BCE'
        # negative start date and positive end date
        span.start_year = -50
        span.end_year = 20
        assert span.dates == '50 BCE-20 CE'
        # negative start and end date
        span.start_year = -150
        span.end_year = -100
        assert span.dates == '150-100 BCE'
        # identical negative dates
        span.start_year = span.end_year = -100
        assert span.dates == '100 BCE'

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

    def test_aliasing(self):
        class TestModel(DateRange):
            foo_year = AliasIntegerField(db_column='start_year')
            bar_year = AliasIntegerField(db_column='end_year')
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


class TestVerifyLatLon(TestCase):

    def test_verifylatlon(self):

        # Django catches wrong type input already, so we can be safe that it
        # will be integer or float

        # OK
        verify_latlon(156.677)
        # Also OK
        verify_latlon(-156.23)
        # Not OK
        with pytest.raises(ValidationError) as err:
            verify_latlon(-181)
        assert 'Lat/Lon must be between -180 and 180 degrees.' in str(err)

        # Still not OK
        with pytest.raises(ValidationError) as err:
            verify_latlon(200)
        assert 'Lat/Lon must be between -180 and 180 degrees.' in str(err)


class TestLocalUserAdmin(TestCase):

    def test_group_names(self):
        localadmin = LocalUserAdmin(User, Mock())  # 2nd arg is admin site
        user = User.objects.create()
        assert localadmin.group_names(user) is None

        grp1 = Group.objects.create(name='Admins')
        grp2 = Group.objects.create(name='Staff')
        user.groups.add(grp1)
        user.groups.add(grp2)
        assert localadmin.group_names(user) == 'Admins, Staff'



class TestAdminDashboard(TestCase):

    def test_dashboard(self):
        # create admin user who can view the admin dashboard
        su_password = 'itsasecret'
        superuser = User.objects.create_superuser(username='admin',
            password=su_password, email='su@example.com')
        # login as admin user
        self.client.login(username=superuser.username, password=su_password)

        response = self.client.get(reverse('admin:index'))
        # check expected order
        response_content = response.content.decode()
        # accounts before personography
        assert re.search('Library Accounts.*Personography',
                         response_content, flags=re.MULTILINE|re.DOTALL)
        # personography before bibliography
        assert re.search('Personography.*Bibliography',
                         response_content, flags=re.MULTILINE|re.DOTALL)
        # bibliography before footnotes
        assert re.search('Bibliography.*Footnotes',
                         response_content, flags=re.MULTILINE|re.DOTALL)
        # bibliography before footnotes
        assert re.search('Footnotes.*Administration',
                         response_content, flags=re.MULTILINE|re.DOTALL)

        # spot check a few expected urls
        for admin_url in ['people_person_changelist', 'accounts_account_changelist',
                          'accounts_borrow_changelist', 'footnotes_footnote_changelist',
                          'books_item_changelist']:
            assert reverse('admin:%s' % admin_url) in response_content


