import re
import uuid
from collections import OrderedDict
from unittest.mock import Mock, patch

import pytest
import rdflib
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Model
from django.http import Http404, HttpRequest, JsonResponse, QueryDict
from django.template.loader import get_template
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse
from django.views.generic.list import ListView
from piffle.iiif import IIIFImageClient

from mep.accounts.models import Account, Event
from mep.common import SCHEMA_ORG, views
from mep.common.admin import LocalUserAdmin
from mep.common.forms import (CheckboxFieldset, FacetChoiceField, FacetForm,
                              RangeField, RangeWidget)
from mep.common.management.export import BaseExport, StreamArray
from mep.common.models import AliasIntegerField, DateRange, Named, Notable
from mep.common.templatetags import mep_tags
from mep.common.utils import absolutize_url, alpha_pagelabels
from mep.common.validators import verify_latlon
from mep.people.forms import MemberSearchForm
from mep.people.models import Person


class TestNamed(TestCase):

    def test_repr(self):
        named_obj = Named(name='foo')
        assert repr(named_obj) == '<Named %s>' % named_obj.name
        # subclass

        class MyName(Named):
            pass

        mynamed = MyName(name='bar')
        assert repr(mynamed) == '<MyName %s>' % mynamed.name

    def test_str(self):
        named_obj = Named(name='foo')
        assert str(named_obj) == 'foo'


class TestNotable(TestCase):

    def test_has_notes(self):
        noted = Notable()
        assert not noted.has_notes()
        noted.notes = 'some text'
        assert noted.has_notes()
        noted.notes = ''
        assert not noted.has_notes()
        noted.notes = None
        assert not noted.has_notes()

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
        assert span.dates == '1900 – 1901'
        # start and end dates are same year = single year
        span.end_year = span.start_year
        assert span.dates == str(span.start_year)
        # start date but no end
        span.end_year = None
        assert span.dates == '1900 –'
        # end date but no start
        span.end_year = 1950
        span.start_year = None
        assert span.dates == '– 1950'
        # negative start date but no end
        span.start_year = -150
        span.end_year = None
        assert span.dates == '150 BCE –'
        # negative end date but no start
        span.start_year = None
        span.end_year = -201
        assert span.dates == '– 201 BCE'
        # negative start date and positive end date
        span.start_year = -50
        span.end_year = 20
        assert span.dates == '50 BCE – 20 CE'
        # negative start and end date
        span.start_year = -150
        span.end_year = -100
        assert span.dates == '150 – 100 BCE'
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
        # get with no instance should return the descriptor object
        class TestModel(DateRange):
            foo_year = AliasIntegerField(db_column='start_year')

        assert isinstance(TestModel.foo_year, AliasIntegerField)


class TestVerifyLatLon(TestCase):

    def test_verifylatlon(self):

        # Django catches wrong type input already, so we can be safe that it
        # will be integer or float

        # OK
        verify_latlon(156.677)
        # Also OK
        verify_latlon(-156.23)
        # Not OK
        with pytest.raises(ValidationError) as excinfo:
            verify_latlon(-181)
        assert 'Lat/Lon must be between -180 and 180 degrees.' in \
            str(excinfo.value)

        # Still not OK
        with pytest.raises(ValidationError) as excinfo:
            verify_latlon(200)
        assert 'Lat/Lon must be between -180 and 180 degrees.' in \
            str(excinfo.value)


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
        su_password = str(uuid.uuid4())
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
                          'books_work_changelist']:
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
    class Item:
        def __init__(self, title):
            self.title = title
    titles = ['Abigail', 'Abner', 'Adam', 'Allen', 'Amy', 'Andy',
              'Annabelle', 'Anne', 'Azad']
    items = [Item(t) for t in titles]
    paginator = Paginator(items, per_page=2)
    labels = alpha_pagelabels(paginator, items, lambda x: getattr(x, 'title'))
    assert labels[1] == 'Abi – Abn'
    assert labels[2] == 'Ad – Al'
    assert labels[3] == 'Am – And'
    assert labels[4] == 'Anna – Anne'
    assert labels[5] == 'Az'

    # with max chars option
    labels = alpha_pagelabels(paginator, items, lambda x: getattr(x, 'title'),
                              max_chars=3)
    assert labels[1] == 'Abi – Abn'
    assert labels[2] == 'Ada – All'
    assert labels[3] == 'Amy – And'
    assert labels[4] == 'Ann – Ann'
    assert labels[5] == 'Aza'

    # exact match on labels for page boundary
    titles.insert(1, 'Abner')
    items = [Item(t) for t in titles]
    labels = alpha_pagelabels(paginator, items, lambda x: getattr(x, 'title'))
    assert labels[1].endswith('– Abner')
    assert labels[2].startswith('Abner –')

    # single page of results - use first and last for labels
    paginator = Paginator(items, per_page=20)
    labels = alpha_pagelabels(paginator, items, lambda x: getattr(x, 'title'))
    assert len(labels) == 1
    # first two letters of first and last titles is enough
    assert labels[1] == '%s – %s' % (titles[0][:2], titles[-1][:2])

    # returns empty response if no items
    paginator = Paginator([], per_page=20)
    assert not alpha_pagelabels(paginator, [], lambda x: getattr(x, 'title'))

    # case-insensitive
    titles = ['Core', 'd\'Aricourt', 'D\'Assay', 'Estaing']
    items = [Item(t) for t in titles]
    paginator = Paginator(items, per_page=2)
    labels = alpha_pagelabels(paginator, items, lambda x: getattr(x, 'title'))
    assert labels[1].endswith("d'Ar")
    assert labels[2].startswith("D'As")


class TestLabeledPagesMixin(TestCase):

    def test_get_page_labels(self):

        class MyLabeledPagesView(views.LabeledPagesMixin, ListView):
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
        assert context['page_labels'][-1] == (7, '31 – 33')
        # with no items, should return an empty list
        view.object_list = []
        view.request = rf.get('/', {'page': '1'})
        context = view.get_context_data()
        assert context['page_labels'] == []

    def test_dispatch(self):

        class MyLabeledPagesView(views.LabeledPagesMixin, ListView):
            paginate_by = 5

        view = MyLabeledPagesView()
        # create some page labels
        view._page_labels = [(1, '1 – 5'), (2, '6 – 10')]
        # make an ajax request
        view.request = Mock()
        view.request.is_ajax.return_value = True
        response = view.dispatch(view.request)
        # should return serialized labels using '|' separator and using hyphen
        # instead of en dash to avoid sending unicode via http header
        assert response['X-Page-Labels'] == '1 - 5|6 - 10'


# tests for template tags


def test_dict_item():
    # no error on not found
    assert mep_tags.dict_item({}, 'foo') is None
    # string key
    assert mep_tags.dict_item({'foo': 'bar'}, 'foo') == 'bar'
    # integer key
    assert mep_tags.dict_item({13: 'lucky'}, 13) == 'lucky'
    # integer value
    assert mep_tags.dict_item({13: 7}, 13) == 7


def test_domain():
    # works correctly on URLs that have both a domain and //
    assert mep_tags.domain('https://docs.python.org/3/library/') == 'python'
    assert mep_tags.domain('//www.cwi.nl:80/%7Eguido/Python.html') == 'cwi'
    # returns None on local URLs or those missing //
    assert mep_tags.domain('www.cwi.nl/%7Eguido/Python.html') is None
    assert mep_tags.domain('help/Python.html') is None
    # returns None on garbage
    assert mep_tags.domain('oops') is None
    assert mep_tags.domain(2) is None
    assert mep_tags.domain(None) is None


def test_iiif_image():
    myimg = IIIFImageClient('http://image.server/path/', 'myimgid')
    # check expected behavior
    assert str(mep_tags.iiif_image(myimg, 'size:width=250')) == \
        str(myimg.size(width=250))
    assert str(mep_tags.iiif_image(myimg, 'size:width=250,height=300')) == \
        str(myimg.size(width=250, height=300))
    assert str(mep_tags.iiif_image(myimg, 'format:png')) == \
        str(myimg.format('png'))

    # check that errors don't raise exceptions
    assert mep_tags.iiif_image(myimg, 'bogus') == ''
    assert mep_tags.iiif_image(myimg, 'size:bogus') == ''
    assert mep_tags.iiif_image(myimg, 'size:bogus=1') == ''


@pytest.mark.django_db
def test_partialdate_filter():
    # None should return None
    assert mep_tags.partialdate(None, 'c') is None
    # unset date should return None
    acct = Account.objects.create()
    evt = Event.objects.create(account=acct)
    assert mep_tags.partialdate(evt.partial_start_date, 'c') is None

    # test with ap date format as default
    with override_settings(DATE_FORMAT='N j, Y'):
        # year only
        evt.partial_start_date = '1934'
        assert mep_tags.partialdate(evt.partial_start_date) == '1934'
        # year and month
        evt.partial_start_date = '1934-02'
        assert mep_tags.partialdate(evt.partial_start_date) == 'Feb. 1934'
        # month and day
        evt.partial_start_date = '--03-06'
        assert mep_tags.partialdate(evt.partial_start_date) == 'March 6'
        # full precision
        evt.partial_start_date = '1934-11-06'
        assert mep_tags.partialdate(evt.partial_start_date) == 'Nov. 6, 1934'

    # partial precision with trailing punctuation in the date
    evt.partial_start_date = '--11-26'
    assert mep_tags.partialdate(evt.partial_start_date, 'j N') == '26 Nov.'

    # check a different format
    evt.partial_start_date = '--11-26'
    assert mep_tags.partialdate(evt.partial_start_date, 'Ymd') == '1126'
    evt.partial_start_date = '1932-11'
    assert mep_tags.partialdate(evt.partial_start_date, 'Ymd') == '193211'
    evt.partial_start_date = '1932'
    assert mep_tags.partialdate(evt.partial_start_date, 'Ymd') == '1932'

    # check week format
    evt.partial_start_date = '1922-01-06'
    assert mep_tags.partialdate(evt.partial_start_date, 'W y') == '1 22'
    evt.partial_start_date = '--01-06'
    assert mep_tags.partialdate(evt.partial_start_date, 'W y') is None

    # handle error in parsing date
    assert mep_tags.partialdate('foobar', 'Y-m-d') is None


def test_querystring_remove():
    # single value by key
    qs = mep_tags.querystring_remove(QueryDict('a=1&b=2'), 'a')
    assert 'a' not in qs
    assert qs['b'] == '2'
    # multiple values by key
    qs = mep_tags.querystring_remove(QueryDict('a=1&b=2'), 'a', 'b')
    assert not qs   # empty string
    # one of a multivalue
    qs = mep_tags.querystring_remove(QueryDict('a=1&a=2&a=3'), a='2')
    assert qs.urlencode() == 'a=1&a=3'


def test_querystring_minus():
    querystring = QueryDict('a=1&b=2&c=3')
    context = {'request': Mock(GET=querystring)}
    qs = mep_tags.querystring_minus(context, 'a', 'c')
    assert qs == QueryDict('b=2')
    qs = mep_tags.querystring_minus(context, 'a', 'b', 'c')
    assert qs == QueryDict()


def test_querystring_only():
    querystring = QueryDict('a=1&b=2&c=3')
    context = {'request': Mock(GET=querystring)}
    qs = mep_tags.querystring_only(context, 'a', 'c')
    assert qs == QueryDict('a=1&c=3')
    qs = mep_tags.querystring_only(context, 'b')
    assert qs == QueryDict('b=2')


def test_formfield_selected_filter():
    form = MemberSearchForm(data={
        'has_card': 1,
        'membership_dates_0': 1920,
        'birth_year_1': 1950,
        'gender': ['Female', 'Male'],
    })
    form.set_choices_from_facets(
        {'gender': OrderedDict([('Female', 0), ('Male', 0)])})

    querystring = QueryDict('has_card=1&page=2&sort=relevance&query=stein')
    context = {'request': Mock(GET=querystring)}
    # boolean field
    link = mep_tags.formfield_selected_filter(context, form['has_card'])
    # still on python 3.5, can't assume order doesn't change
    # assert link == '<a href="?sort=relevance&query=stein">Card</a>'
    assert link.startswith('<a data-input="id_has_card" href="?')
    assert link.endswith('">Card</a>')
    for query_param in ['sort=relevance', 'query=stein']:
        assert query_param in link
    assert 'has_card=1' not in link

    # range field - first date only
    querystring = QueryDict('has_card=1&page=2&sort=relevance&query=stein' +
                            '&membership_dates_0=1920&membership_dates_1=test')
    context = {'request': Mock(GET=querystring)}
    link = mep_tags.formfield_selected_filter(context,
                                              form['membership_dates'])
    assert "Membership Years 1920 – &nbsp;" in link
    for query_param in ['sort=relevance', 'query=stein', 'has_card=1']:
        assert query_param in link
    for membership_param in ['membership_dates_0', 'membership_dates_1']:
        assert membership_param not in link
    # assert 'href="?has_card=1&sort=relevance&query=stein"' in link

    # range field - second date only
    querystring = QueryDict('query=stein&birth_year_0=&birth_year_1=1950')
    context = {'request': Mock(GET=querystring)}

    link = mep_tags.formfield_selected_filter(context,
                                              form['birth_year'])
    assert "Birth Year &nbsp; – 1950" in link
    assert 'href="?query=stein"' in link
    for birth_param in ['birth_year_0', 'birth_year_1']:
        assert birth_param not in link

    # facet choice field with multiple values
    querystring = QueryDict('query=stein&gender=Female&gender=Male')
    context = {'request': Mock(GET=querystring)}
    link = mep_tags.formfield_selected_filter(context,
                                              form['gender'])
    # generates two links; each preserves the *other* filter
    # NOTE: [^>]* pattern is to ignore data-input attribute
    assert re.search(r'<a[^>]*href="\?[^"]*gender=Male[^"]*">Female</a>', link)
    assert re.search(r'<a[^>]*href="\?[^"]*gender=Female[^"]*">Male</a>', link)
    assert not re.search(r'<a[^>]*href="\?[^"]*gender=Female[^"]*">Female</a>',
                         link)
    assert not re.search(r'<a[^>]*href="\?[^"]*gender=Male[^"]*">Male</a>',
                         link)
    # assert '<a href="?query=stein&gender=Female">Male</a>' in link

    # don't blow up on invalid facet
    form = MemberSearchForm(data={
        'nationality': 'foobar'
    })
    querystring = QueryDict('query=stein&nationality=foobar')
    context = {'request': Mock(GET=querystring)}
    # no facets set on the form - should be an empty link
    assert not mep_tags.formfield_selected_filter(context,
                                                  form['nationality'])
    form.set_choices_from_facets(
        {'nationality': OrderedDict([('Argentina', 0), ('Chile', 0)])})
    # form has an invalid link - should be an empty link
    assert not mep_tags.formfield_selected_filter(context,
                                                  form['nationality'])


class TestCheckboxFieldset(TestCase):

    def test_get_context(self):
        checkbox_fieldset = CheckboxFieldset()
        checkbox_fieldset.legend = 'Test Legend'
        checkbox_fieldset.facet_counts = {'value': 10}
        context = checkbox_fieldset.get_context('a name', ['a', 'b', 'c'], {})
        assert context['widget']['legend'] == 'Test Legend'
        assert context['facet_counts'] == checkbox_fieldset.facet_counts

    def test_render(self):

        # make sure that legend is rendered based on a custom property
        checkbox_fieldset = CheckboxFieldset()
        # set legend and id for test purposes
        checkbox_fieldset.legend = 'Foo'
        checkbox_fieldset.attrs['id'] = 'widget_id'

        checkbox_fieldset.optgroups = Mock()
        # mock a substitute for the return value of optgroups
        # The reasons for this are two fold:
        #   1) The logic of how widgets are populated is fairly convoluted, and
        #       we're only checking that the template does the right thing here.
        #   2) optgroups is a function and needs a mock to supply the return.
        checkbox_fieldset.optgroups.return_value = [
            (
                None,
                [
                    {
                        'label': 'A',
                        # ensure that checked value is respected
                        # id is set
                        # and value and label are not synonymous
                        'attrs': {'checked': True, 'id': 'id_for_0'},
                        'value': 'a'
                    },
                    {
                        'label': 'B',
                        'attrs': {'id': 'id_for_1'},
                        'value': 'b'
                    }
                ],
                0
            )
        ]
        # first arg sets the name attribute, other is unused after optgroup
        # override
        out = checkbox_fieldset.render('gender', 'bar')
        # legend should be upper-cased by default
        expected_output = '''
        <fieldset id="widget_id" tabindex="0">
            <legend>Foo</legend>
            <ul class="choices">
            <li class="choice">
            <input type="checkbox" value="a" id="id_for_0" name="gender" checked />
           <label for="id_for_0"> A </label>
           </li>
           <li class="choice">
           <input type="checkbox" value="b" id="id_for_1" name="gender" />
           <label for="id_for_1"> B </label>
           </li>
           </ul>
        </fieldset>
        '''
        self.assertHTMLEqual(out, expected_output)
        # if required is set, each input should have required set
        checkbox_fieldset.is_required = True
        out = checkbox_fieldset.render('foo', 'bar')
        assert out.count('required') == 2

        checkbox_fieldset.attrs['data-hide-threshold'] = 0
        checkbox_fieldset.facet_counts = {'a': 0, 'b': 2}
        output = checkbox_fieldset.render('gender', 'bar')
        assert 'data-hide-threshold="0"' in output
        # a choice should be hidden
        assert '<li class="choice hide">' in output
        # b choice should not be hidden
        assert '<li class="choice">' in output


class TestFacetField(TestCase):

    def test_init(self):

        # value of required is passed through on init
        facet_field = FacetChoiceField(required=True)
        assert facet_field.required
        # if not set, defaults to false
        facet_field = FacetChoiceField()
        assert not facet_field.required
        # check that legend is set via label separately
        facet_field = FacetChoiceField(label='Test')
        assert facet_field.widget.legend == 'Test'
        # but widget attrs overrules
        facet_field = FacetChoiceField(label='Test', legend='NotTest')
        assert facet_field.widget.legend == 'NotTest'

    def test_valid_value(self):
        # any value passed in returns true
        facet_field = FacetChoiceField()
        assert facet_field.valid_value('A') is True
        assert facet_field.valid_value(10) is True


class TestFacetForm(TestCase):

    def test_set_choices_from_facets(self):

        # Create a test form with mappings
        class TestForm(FacetForm):

            solr_facet_fields = {
                'name_s': 'name'
            }

            name = FacetChoiceField()
            member_type = FacetChoiceField()

        test_form = TestForm()

        # create facets in the format provided by parasolr
        facets = OrderedDict()
        facets['name_s'] = OrderedDict([('Jane', 2000), ('John', 1)])
        facets['member_type'] = OrderedDict([('weekly', 2), ('monthly', 1)])
        # handling should not choke on an unhandled field
        facets['unhandled_fields'] = OrderedDict(foo=1, bar=1)

        test_form.set_choices_from_facets(facets)

        # no mapping but matching field should be rendered
        assert test_form.fields['member_type'].choices == [
            ('weekly', 'weekly<span class="count">2</span>'),
            ('monthly', 'monthly<span class="count">1</span>'),
        ]
        # mapping should convert solr field name to form field name
        assert test_form.fields['name'].choices == [
            # check that comma formatting appears as expected
            ('Jane', 'Jane<span class="count">2,000</span>'),
            ('John', 'John<span class="count">1</span>')
        ]
        # unhandled field should not be passed in
        assert 'unhanded_field' not in test_form.fields


class TestVaryOnHeadersMixin(TestCase):

    def test_vary_on_headers_mixing(self):

        # stub a View that will always return 405 since no methods are defined
        vary_on_view = \
            views.VaryOnHeadersMixin(vary_headers=['X-Foobar', 'X-Bazbar'])
        # mock a request because we don't need its functionality
        request = Mock()
        response = vary_on_view.dispatch(request)
        # check for the set header with the values supplied
        assert response['Vary'] == 'X-Foobar, X-Bazbar'


class TestAjaxTemplateMixin(TestCase):

    def test_get_templates(self):
        class MyAjaxyView(views.AjaxTemplateMixin):
            ajax_template_name = 'my_ajax_template.json'
            template_name = 'my_normal_template.html'

        myview = MyAjaxyView()
        myview.request = Mock()
        myview.request.is_ajax.return_value = False
        assert myview.get_template_names() == [MyAjaxyView.template_name]

        myview.request.is_ajax.return_value = True
        assert myview.get_template_names() == MyAjaxyView.ajax_template_name


class TestFacetJSONMixin(TestCase):

    def test_render_response(self):
        class MyViewWithFacets(views.FacetJSONMixin):
            template_name = 'my_normal_template.html'

        # create a mock request and queryset
        view = MyViewWithFacets()
        view.object_list = Mock()
        view.object_list.get_facets.return_value = {
            'facets': 'foo'
        }
        view.request = HttpRequest()
        request = Mock()

        # if no Accept: header, should just return a regular response
        view.request.META['HTTP_ACCEPT'] = ''
        response = view.render_to_response(request)
        assert not isinstance(response, JsonResponse)

        # if header is set to 'application/json', should be json response
        view.request.META['HTTP_ACCEPT'] = 'application/json'
        response = view.render_to_response(request)
        assert isinstance(response, JsonResponse)
        assert response.content == b'{"facets": "foo"}'


class TestLoginRequiredOr404Mixin(TestCase):

    def test_handle_no_permission(self):
        with pytest.raises(Http404):
            views.LoginRequiredOr404Mixin().handle_no_permission()


# range widget and field tests copied from derrida via ppa

def test_range_widget():
    # range widget decompress logic
    assert RangeWidget().decompress((None, None)) == [None, None]
    assert RangeWidget().decompress(None) == [None, None]
    assert RangeWidget().decompress((100, None)) == [100, None]
    assert RangeWidget().decompress((None, 250)) == [None, 250]
    assert RangeWidget().decompress((100, 250)) == [100, 250]
    assert RangeWidget().decompress(('100', '250')) == [100, 250]


def test_range_field():
    # range widget decompress logic
    assert RangeField().compress([]) is None
    assert RangeField().compress([100, None]) == (100, None)
    assert RangeField().compress([None, 250]) == (None, 250)
    assert RangeField().compress([100, 250]) == (100, 250)

    # out of order should raise exception
    with pytest.raises(ValidationError):
        RangeField().compress([200, 100])

    # test_set_min_max
    rangefield = RangeField()
    rangefield.set_min_max(1910, 1930)
    assert rangefield.widget.attrs['min'] == 1910
    assert rangefield.widget.attrs['max'] == 1930
    start_widget, end_widget = rangefield.widget.widgets
    assert start_widget.attrs['placeholder'] == 1910
    assert end_widget.attrs['placeholder'] == 1930


class TestRdfViewMixin(TestCase):

    def test_get_absolute_url(self):
        class MyRdfView(views.RdfViewMixin):
            pass
        view = MyRdfView()
        # get_absolute_url() not implemented by default
        with pytest.raises(NotImplementedError):
            view.get_absolute_url()

    def test_get_breadcrumbs(self):
        class MyRdfView(views.RdfViewMixin):
            breadcrumbs = [('Home', '/'), ('My Page', '/my-page')]

            def get_absolute_url(self):
                return ''

        view = MyRdfView()
        # should add provided breadcrumbs to context
        context = view.get_context_data()
        assert context['breadcrumbs'] == [('Home', '/'),
                                          ('My Page', '/my-page')]
        # should be string and not bytes, to render properly
        assert isinstance(context['page_jsonld'], str)

    def test_rdf_graph(self):
        class MyRdfView(views.RdfViewMixin):
            breadcrumbs = [('Home', '/'), ('My Page', '/my-page')]

            def get_absolute_url(self):
                return 'http://jimcasey.lifestyle/my-page'

        view = MyRdfView()
        graph = view.as_rdf()
        page_node = rdflib.URIRef('http://jimcasey.lifestyle/my-page')
        # should have root node as URIRef to the page with default type WebPage
        assert (page_node,
                rdflib.RDF.type,
                SCHEMA_ORG.WebPage) in graph
        # should have (blank) nodes with URIs for each of the breadcrumbs
        # any=False will raise an exception unless we find exactly one match
        home_crumb = graph.value(predicate=SCHEMA_ORG.item,
                                 object=rdflib.Literal('/'),
                                 any=False)
        page_crumb = graph.value(predicate=SCHEMA_ORG.item,
                                 object=rdflib.Literal('/my-page'),
                                 any=False)
        # crumbs should have the correct name and position values
        assert graph.value(home_crumb, SCHEMA_ORG.name) == \
            rdflib.Literal('Home')
        assert graph.value(page_crumb, SCHEMA_ORG.name) == \
            rdflib.Literal('My Page')
        assert graph.value(home_crumb, SCHEMA_ORG.position) == \
            rdflib.Literal(1)
        assert graph.value(page_crumb, SCHEMA_ORG.position) == \
            rdflib.Literal(2)
        # page should have breadcrumb list
        crumb_list = graph.value(page_node, SCHEMA_ORG.breadcrumb, any=False)
        # crumbs should belong to the list as itemListElements
        assert (crumb_list, SCHEMA_ORG.itemListElement, home_crumb) in graph
        assert (crumb_list, SCHEMA_ORG.itemListElement, page_crumb) in graph


class TestBreadcrumbsTemplate(TestCase):

    def setUp(self):
        # get the template
        self.template = get_template('snippets/breadcrumbs.html')

    def test_home(self):
        # without a 'home' crumb
        response = self.template.render(context={
            'breadcrumbs': [('My Page', '/my-page')]
        })
        assert '<li class="home">' not in response
        # with a 'home' crumb
        response = self.template.render(context={
            'breadcrumbs': [('Home', '/')]
        })
        assert '<li class="home">' in response

    def test_last_crumb(self):
        response = self.template.render(context={
            'breadcrumbs': [
                ('Home', '/'),
                ('My Page', '/my-page')
            ]
        })
        # normal crumbs should be <a>
        assert "<a href=\"/\">Home</a>" in response
        # final crumb should be <span>
        assert "<span>My Page</span>" in response


class TestBaseExport(TestCase):

    def test_flatten_dict(self):
        # flat dict should not be changed
        flat = {'one': 'a', 'two': 'b'}
        assert flat == BaseExport.flatten_dict(flat)

        # list should be converted to string
        listed = {'one': ['a', 'b']}
        flat_listed = BaseExport.flatten_dict(listed)
        assert flat_listed['one'] == 'a;b'

        # nested dict should have keys combined and be flatted
        nested = {
            'page': {
                'id': 'p1',
                'label': 'one'
            }
        }
        flat_nested = BaseExport.flatten_dict(nested)
        assert 'page_id' in flat_nested
        assert 'page_label' in flat_nested
        assert flat_nested['page_id'] == nested['page']['id']
        assert flat_nested['page_label'] == nested['page']['label']

        # nested with list
        nested_list = {
            'page': {
                'id': 'p1',
                'label': ['one', 'two']
            }
        }
        flat_nested = BaseExport.flatten_dict(nested_list)
        assert flat_nested['page_label'] == 'one;two'

        # handle list of integer
        nested_list['page']['label'] = [1, 2, 3]
        flat_nested = BaseExport.flatten_dict(nested_list)
        assert flat_nested['page_label'] == '1;2;3'


@patch('mep.common.management.export.progressbar')
class TestStreamArray(TestCase):

    def test_init(self, mockprogbar):
        total = 5
        gen = (i for i in range(total))

        streamer = StreamArray(gen, total)
        assert streamer.gen == gen
        assert streamer.progress == 0
        assert streamer.total == total

        mockprogbar.ProgressBar.assert_called_with(redirect_stdout=True,
                                                   max_value=total)
        assert streamer.progbar == mockprogbar.ProgressBar.return_value

    def test_len(self, mockprogbar):
        total = 5
        gen = (i for i in range(total))
        streamer = StreamArray(gen, total)
        assert len(streamer) == total

    def test_iter(self, mockprogbar):
        total = 2
        gen = (i for i in range(total))
        streamer = StreamArray(gen, total)
        values = []
        for val in streamer:
            values.append(val)

        assert values == [i for i in range(total)]
        assert streamer.progress == total
        # progress bar update should be called once per item
        assert streamer.progbar.update.call_count == total
        # progress bar finish should be called once when iteration completes
        assert streamer.progbar.finish.call_count == 1


class TestTrackChangesModel(TestCase):
    # track changes functions tested via Person subclass

    def setUp(self):
        self.instance = Person.objects.create(slug='old')

    def test_has_changed(self):
        person = Person.objects.get(pk=self.instance.pk)
        # no modifications
        assert not person.has_changed('slug')
        # changed
        person.slug = 'new'
        assert person.has_changed('slug')

    def test_initial_value(self):
        person = Person.objects.get(pk=self.instance.pk)
        assert person.initial_value('slug') == 'old'
        # set a new valuef
        person.slug = 'new'
        # should still return the same initial value
        assert person.initial_value('slug') == 'old'

    def test_save(self):
        person = Person.objects.get(pk=self.instance.pk)
        person.slug = 'new'
        person.save()
        # should not detect as changed after save
        assert not person.has_changed('slug')
