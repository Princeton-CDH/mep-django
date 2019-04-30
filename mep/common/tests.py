import re
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse
from django.views.generic.list import ListView

from mep.common.admin import LocalUserAdmin
from mep.common.models import AliasIntegerField, DateRange, Named, Notable
from mep.common.utils import absolutize_url, alpha_pagelabels
from mep.common.validators import verify_latlon
from mep.common.views import LabeledPagesMixin, VaryOnHeadersMixin, AjaxTemplateMixin
from mep.common.templatetags.mep_tags import dict_item

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
        assert span.dates == '1900-1901'
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

    def test_clean(self):
        with pytest.raises(ValidationError):
            DateRange(start_year=1901, end_year=1900).clean()

        # should not raise exception
        # - same year is ok (single year range)
        DateRange(start_year=1901, end_year=1901).clean()
        # - end after start
        DateRange(start_year=1901, end_year=1905).clean()
        # - only one date set
        DateRange(start_year=1901).clean()
        DateRange(end_year=1901).clean()


class TestAliasIntegerField(TestCase):

    def test_aliasing(self):
        class TestModel(DateRange):
            foo_year = AliasIntegerField(db_column='start_year')
            bar_year = AliasIntegerField(db_column='end_year')
        # Should pass the exact same tests as date range with the new fields
        with pytest.raises(ValidationError):
            TestModel(foo_year=1901, bar_year=1900).clean()

        # should not raise exception
        # - same year is ok (single year range)
        TestModel(foo_year=1901, bar_year=1901).clean()
        # - end after start
        TestModel(foo_year=1901, bar_year=1905).clean()
        # - only one date set
        TestModel(foo_year=1901).clean()
        TestModel(bar_year=1901).clean()

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


@pytest.mark.django_db
def test_absolutize_url():
    https_url = 'https://example.com/some/path/'
    # https url is returned unchanged
    assert absolutize_url(https_url) == https_url
    # testing with default site domain
    current_site = Site.objects.get_current()

    # test site domain without https
    current_site.domain = 'example.org'
    current_site.save()
    local_path = '/foo/bar/'
    assert absolutize_url(local_path) == 'https://example.org/foo/bar/'
    # trailing slash in domain doesn't result in double slash
    current_site.domain = 'example.org/'
    current_site.save()
    assert absolutize_url(local_path) == 'https://example.org/foo/bar/'
    # site at subdomain should work too
    current_site.domain = 'example.org/sub/'
    current_site.save()
    assert absolutize_url(local_path) == 'https://example.org/sub/foo/bar/'
    # site with https:// included
    current_site.domain = 'https://example.org'
    assert absolutize_url(local_path) == 'https://example.org/sub/foo/bar/'


    with override_settings(DEBUG=True):
        assert absolutize_url(local_path) == 'https://example.org/sub/foo/bar/'
        mockrqst = Mock(scheme='http')
        assert absolutize_url(local_path, mockrqst) == \
            'http://example.org/sub/foo/bar/'



def test_alpha_pagelabels():
    # create minimal object and list of items to generate labels for
    class item:
        def __init__(self, title):
            self.title = title
    titles = ['Abigail', 'Abner', 'Adam', 'Allen', 'Amy', 'Andy', 'Annabelle', 'Anne', 'Azad']
    items = [item(t) for t in titles]
    paginator = Paginator(items, per_page=2)
    labels = alpha_pagelabels(paginator, items, lambda x: getattr(x, 'title'))
    assert labels[1] == 'Abi - Abn'
    assert labels[2] == 'Ad - Al'
    assert labels[3] == 'Am - And'
    assert labels[4] == 'Anna - Anne'
    assert labels[5] == 'Az'

    # exact match on labels for page boundary
    titles.insert(1, 'Abner')
    items = [item(t) for t in titles]
    labels = alpha_pagelabels(paginator, items, lambda x: getattr(x, 'title'))
    assert labels[1].endswith('- Abner')
    assert labels[2].startswith('Abner - ')

    # single page of results - use first and last for labels
    paginator = Paginator(items, per_page=20)
    labels = alpha_pagelabels(paginator, items, lambda x: getattr(x, 'title'))
    assert len(labels) == 1
    # first two letters of first and last titles is enough
    assert labels[1] == '%s - %s' % (titles[0][:2], titles[-1][:2])

    # returns empty response if no items
    paginator = Paginator([], per_page=20)
    assert not alpha_pagelabels(paginator, [], lambda x: getattr(x, 'title'))


class TestLabeledPagesMixin(TestCase):

    def test_get_page_labels(self):

        class MyLabeledPagesView(LabeledPagesMixin, ListView):
            paginate_by = 5

        view = MyLabeledPagesView()
        rf = RequestFactory()
        # populating some properties directly to skip the dispatch flow
        view.object_list = list(range(0, 33))
        view.kwargs = {}
        view.request = rf.get('/', {'page': '1'})
        context = view.get_context_data()
        # should have page labels in context
        assert 'page_labels' in context
        # should be 7 pages of 5 items each
        assert len(context['page_labels']) == 7
        # last page label shows only the remaining items
        assert context['page_labels'][-1] == (7, '31 - 33')
        # with no items, should return an empty list
        view.object_list = []
        view.request = rf.get('/', {'page': '1'})
        context = view.get_context_data()
        assert context['page_labels'] == []

    def test_dispatch(self):

        class MyLabeledPagesView(LabeledPagesMixin, ListView):
            paginate_by = 5

        view = MyLabeledPagesView()
        # create some page labels
        view._page_labels = [(1, '1-5'), (2, '6-10')]
        # make an ajax request
        view.request = Mock()
        view.request.is_ajax.return_value = True
        response = view.dispatch(view.request)
        # should return serialized labels using '|' separator
        assert response['X-Page-Labels'] == '1-5|6-10'


class TestTemplateTags(TestCase):

    def test_dict_item(self):
        # no error on not found
        assert dict_item({}, 'foo') is None
        # string key
        assert dict_item({'foo': 'bar'}, 'foo') is 'bar'
        # integer key
        assert dict_item({13: 'lucky'}, 13) is 'lucky'
        # integer value
        assert dict_item({13: 7}, 13) is 7


class TestVaryOnHeadersMixin(TestCase):

    def test_vary_on_headers_mixing(self):

        # stub a View that will always return 405 since no methods are defined
        vary_on_view = \
            VaryOnHeadersMixin(vary_headers=['X-Foobar', 'X-Bazbar'])
        # mock a request because we don't need its functionality
        request = Mock()
        response = vary_on_view.dispatch(request)
        # check for the set header with the values supplied
        assert response['Vary'] == 'X-Foobar, X-Bazbar'


class TestAjaxTemplateMixin(TestCase):

    def test_get_templates(self):
        class MyAjaxyView(AjaxTemplateMixin):
            ajax_template_name = 'my_ajax_template.json'
            template_name = 'my_normal_template.html'

        myview = MyAjaxyView()
        myview.request = Mock()
        myview.request.is_ajax.return_value = False
        assert myview.get_template_names() == [MyAjaxyView.template_name]

        myview.request.is_ajax.return_value = True
        assert myview.get_template_names() == MyAjaxyView.ajax_template_name