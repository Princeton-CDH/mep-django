import re
from collections import OrderedDict
from unittest.mock import Mock
import uuid

import pytest
import rdflib
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpRequest, JsonResponse
from django.template.loader import get_template
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse
from django.views.generic.list import ListView

from mep.common import SCHEMA_ORG
from mep.common.admin import LocalUserAdmin
from mep.common.forms import CheckboxFieldset, FacetChoiceField, FacetForm, \
    RangeField, RangeWidget
from mep.common.models import AliasIntegerField, DateRange, Named, Notable
from mep.common.templatetags.mep_tags import dict_item
from mep.common.utils import absolutize_url, alpha_pagelabels
from mep.common.validators import verify_latlon
from mep.common.views import AjaxTemplateMixin, FacetJSONMixin, \
    LabeledPagesMixin, RdfViewMixin, VaryOnHeadersMixin


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
        with pytest.raises(AttributeError) as excinfo:
            # simulate passing a None because the object didn't set right
            AliasIntegerField.__get__(AliasIntegerField(), None)
        assert ('Are you trying to set a field that does not '
                'exist on the aliased model?') in str(excinfo.value)


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
        assert dict_item({'foo': 'bar'}, 'foo') == 'bar'
        # integer key
        assert dict_item({13: 'lucky'}, 13) == 'lucky'
        # integer value
        assert dict_item({13: 7}, 13) == 7


class TestCheckboxFieldset(TestCase):

    def test_get_context(self):
        checkbox_fieldset = CheckboxFieldset()
        checkbox_fieldset.legend = 'Test Legend'
        context = checkbox_fieldset.get_context('a name', ['a', 'b', 'c'], {})
        assert context['widget']['legend'] == 'Test Legend'

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
        out = checkbox_fieldset.render('sex', 'bar')
        # legend should be upper-cased by default
        expected_output = '''
        <fieldset id="widget_id">
            <legend>Foo</legend>
            <ul class="choices">
            <li class="choice">
            <input type="checkbox" value="a" id="id_for_0" name="sex" checked />
           <label for="id_for_0"> A </label>
           </li>
           <li class="choice">
           <input type="checkbox" value="b" id="id_for_1" name="sex" />
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


class TestFacetJSONMixin(TestCase):

    def test_render_response(self):
        class MyViewWithFacets(FacetJSONMixin):
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
        class MyRdfView(RdfViewMixin):
            pass
        view = MyRdfView()
        # get_absolute_url() not implemented by default
        with pytest.raises(NotImplementedError):
            view.get_absolute_url()

    def test_get_breadcrumbs(self):
        class MyRdfView(RdfViewMixin):
            breadcrumbs = [('Home', '/'), ('My Page', '/my-page')]
            def get_absolute_url(self):
                return ''
        view = MyRdfView()
        # should add provided breadcrumbs to context
        context = view.get_context_data()
        assert context['breadcrumbs'] == [('Home', '/'), ('My Page', '/my-page')]

    def test_rdf_graph(self):
        class MyRdfView(RdfViewMixin):
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
        assert graph.value(home_crumb, SCHEMA_ORG.name) == rdflib.Literal('Home')
        assert graph.value(page_crumb, SCHEMA_ORG.name) == rdflib.Literal('My Page')
        assert graph.value(home_crumb, SCHEMA_ORG.position) == rdflib.Literal(1)
        assert graph.value(page_crumb, SCHEMA_ORG.position) == rdflib.Literal(2)
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
        assert not '<li class="home">' in response
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
