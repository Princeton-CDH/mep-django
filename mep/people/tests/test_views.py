import json
import time
import uuid
from collections import OrderedDict
from datetime import date
from types import LambdaType
from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser, Permission, User
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.template.defaultfilters import date as format_date
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse
from djiffy.models import Canvas
import pytest

from mep.accounts.models import (Account, Address, Borrow, Event, Purchase,
                                 Reimbursement, Subscription, SubscriptionType)
from mep.accounts.partial_date import DatePrecision
from mep.books.models import Creator, CreatorType, Work
from mep.common.templatetags.mep_tags import partialdate
from mep.common.utils import absolutize_url, login_temporarily_required
from mep.footnotes.models import Bibliography, Footnote, SourceType
from mep.people.admin import GeoNamesLookupWidget, MapWidget
from mep.people.forms import PersonMergeForm
from mep.people.geonames import GeoNamesAPI
from mep.people.models import (Country, Location, Person, Relationship,
                               RelationshipType)
from mep.people.views import (BorrowingActivities, GeoNamesLookup,
                              MemberCardDetail, MemberCardList,
                              MembershipActivities, MembershipGraphs,
                              MembersList, PersonMerge)


class TestPeopleViews(TestCase):

    @patch('mep.people.views.GeoNamesAPI')
    def test_geonames_autocomplete(self, mockgeonamesapi):
        geo_lookup_url = reverse('people:geonames-lookup')
        # abbreviated sample return with fields currently in use
        mock_response = [
            {'name': 'New York City', 'geonameId': 5128581,
             'countryName': 'USA', 'lat': 40.71427, 'lng': -74.00597,
             'countryCode': 'US'}
        ]
        mockgeonamesapi.return_value.search.return_value = mock_response
        # patch in real uri from id logic
        mockgeonamesapi.return_value.uri_from_id = GeoNamesAPI.uri_from_id

        result = self.client.get(geo_lookup_url, {'q': 'new york'})
        assert isinstance(result, JsonResponse)
        assert result.status_code == 200
        mockgeonamesapi.return_value.search.assert_called_with('new york',
            max_rows=50, name_start=True)
        # decode response to inspect
        data = json.loads(result.content.decode('utf-8'))
        # inspect constructed result
        work = data['results'][0]
        assert work['text'] == 'New York City, USA'
        assert work['name'] == 'New York City'
        assert work['lat'] == mock_response[0]['lat']
        assert work['lng'] == mock_response[0]['lng']
        assert work['id'] == \
            GeoNamesAPI.uri_from_id(mock_response[0]['geonameId'])

        # country specific lookup
        country_lookup_url = reverse('people:country-lookup')
        result = self.client.get(country_lookup_url, {'q': 'canada'})
        assert result.status_code == 200
        mockgeonamesapi.return_value.search.assert_called_with('canada',
            feature_class='A', feature_code='PCLI', max_rows=50,
            name_start=True)

    def test_person_autocomplete(self):
        # add a person to search for
        beach = Person.objects.create(name='Sylvia Beach', mep_id='sylv.b',
                                      slug='beach')

        pub_autocomplete_url = reverse('people:autocomplete')
        result = self.client.get(pub_autocomplete_url, {'q': 'beach'})
        assert result.status_code == 200
        # decode response to inspect basic formatting and fields
        data = json.loads(result.content.decode('utf-8'))
        text = data['results'][0]['text']
        self.assertInHTML('<strong>Sylvia Beach</strong> sylv.b', text)

        # no match - shouldn't error, just return no results
        result = self.client.get(pub_autocomplete_url, {'q': 'beauvoir'})
        assert result.status_code == 200
        data = json.loads(result.content.decode('utf-8'))
        assert not data['results']

        # add a person and a title
        ms_sylvia = Person.objects.create(name='Sylvia', title='Ms.',
                                          slug='sylvia')

        # should return both wrapped in <strong>
        result = self.client.get(pub_autocomplete_url, {'q': 'sylvia'})
        assert result.status_code == 200
        # decode response to inspect
        data = json.loads(result.content.decode('utf-8'))
        assert len(data['results']) == 2
        assert 'Sylvia Beach' in data['results'][0]['text']
        # detailed check of Ms. Sylvia
        text = data['results'][1]['text']
        self.assertInHTML('<strong>Ms. Sylvia</strong>', text)

        # should select the right person based on mep_id
        result = self.client.get(pub_autocomplete_url, {'q': 'sylv.b'})
        assert result.status_code == 200
        # decode response to inspect
        data = json.loads(result.content.decode('utf-8'))
        assert len(data['results']) == 1
        assert 'Sylvia Beach' in data['results'][0]['text']

        # add birth, death dates to beach
        beach.birth_year = 1900
        beach.death_year = 1970
        beach.save()
        result = self.client.get(pub_autocomplete_url, {'q': 'sylv.b'})
        # decode response to inspect dates rendered and formatted correctly
        data = json.loads(result.content.decode('utf-8'))
        assert len(data['results']) == 1
        text = data['results'][0]['text']
        expected = '<strong>Sylvia Beach (1900 – 1970)</strong> sylv.b <br />'
        self.assertInHTML(expected, text)

        # add notes to beach
        beach.notes = "All of these words are part of the notes"
        beach.save()
        result = self.client.get(pub_autocomplete_url, {'q': 'sylv.b'})
        data = json.loads(result.content.decode('utf-8'))
        assert len(data['results']) == 1
        text = data['results'][0]['text']
        # first 5 words of notes field should be present in response
        # on a separate line
        expected = ('<strong>Sylvia Beach (1900 – 1970)</strong> '
                    'sylv.b <br />All of these words are')
        self.assertInHTML(expected, text)

        # give Ms. Sylvia a mep id
        ms_sylvia.mep_id = 'sylv.a'
        ms_sylvia.save()
        # check that mep.id shows up in result
        result = self.client.get(pub_autocomplete_url, {'q': 'sylv.a'})
        data = json.loads(result.content.decode('utf-8'))
        text = data['results'][0]['text']
        self.assertInHTML('<strong>Ms. Sylvia</strong> sylv.a', text)
        # give Ms. Sylvia events
        account = Account.objects.create()
        account.persons.add(ms_sylvia)
        Subscription.objects.create(
            account=account,
            start_date=date(1971, 1, 2),
            end_date=date(1971, 1, 31),
        )
        Subscription.objects.create(
            account=account,
            start_date=date(1971, 1, 1),
            end_date=date(1971, 1, 31),
        )
        # first event by start_date should be displayed
        result = self.client.get(pub_autocomplete_url, {'q': 'sylv.a'})
        data = json.loads(result.content.decode('utf-8'))
        text = data['results'][0]['text']
        expected = ('<strong>Ms. Sylvia</strong> sylv.a <br />'
                    'Subscription (1971-01-01 – 1971-01-31)')
        self.assertInHTML(expected, text)

    def test_person_admin_change(self):
        # create user with permission to load admin edit form
        su_password = str(uuid.uuid4())
        superuser = User.objects.create_superuser(username='admin',
            password=su_password, email='su@example.com')

        # login as admin user
        self.client.login(username=superuser.username, password=su_password)

        # create two people and a relationship
        m_dufour = Person.objects.create(name='Charles Dufour', slug='dufour-c')
        mlle_dufour = Person.objects.create(name='Dufour', title='Mlle',
                                            slug='dufour')
        parent = RelationshipType.objects.create(name='parent')
        rel = Relationship.objects.create(from_person=mlle_dufour,
            relationship_type=parent, to_person=m_dufour, notes='relationship uncertain')
        person_edit_url = reverse('admin:people_person_change',
            args=[m_dufour.id])
        result = self.client.get(person_edit_url)
        self.assertContains(result, 'Relationships to this person')
        self.assertContains(result, str(mlle_dufour),
            msg_prefix='should include name of person related to this person ')
        self.assertContains(result, reverse('admin:people_person_change',
            args=[mlle_dufour.id]),
            msg_prefix='should include edit link for person related to this person')
        self.assertContains(result, parent.name,
            msg_prefix='should include relationship name')
        self.assertContains(result, rel.notes,
            msg_prefix='should include any relationship notes')

        # test account information displayed on person edit form
        # - no account
        self.assertContains(result, 'No associated account',
            msg_prefix='indication should be displayed if person has no account')
        # - account but no events
        acct = Account.objects.create()
        acct.persons.add(m_dufour)
        result = self.client.get(person_edit_url)
        self.assertContains(result, str(acct),
            msg_prefix='account label should be displayed if person has one')
        self.assertContains(result,
            reverse('admin:accounts_account_change', args=[acct.id]),
            msg_prefix='should link to account edit page')
        self.assertContains(result, 'No documented subscription or reimbursement events',
            msg_prefix='should display indicator for account with no subscription or reimbursement events')
        # with subscription events
        subs = Subscription.objects.create(account=acct,
            start_date=date(1943, 1, 1), end_date=date(1944, 1, 1))
        subs2 = Subscription.objects.create(account=acct,
            start_date=date(1944, 1, 1),
            subtype=Subscription.RENEWAL)
        reimb = Reimbursement.objects.create(account=acct,
            start_date=date(1944, 2, 1))
        generic = Event.objects.create(account=acct, start_date=date(1940, 1, 1))
        response = self.client.get(person_edit_url)
        # NOTE: template uses django's default date display for locale
        # importing template tag to test with that formatting here
        self.assertContains(response, 'Subscription')
        self.assertContains(response, '%s - %s' % \
            (format_date(subs.start_date), format_date(subs.end_date)))
        self.assertContains(response, 'Renewal')
        self.assertContains(response, '%s - ' % format_date(subs2.start_date))
        # Reimbursement events should be listed
        self.assertContains(response, 'Reimbursement')
        self.assertContains(response, format_date(reimb.start_date))
        # Other event types should not be
        self.assertNotContains(response, 'Generic')
        self.assertNotContains(response, format_date(generic.start_date))

    def test_person_admin_list(self):
        # create user with permission to load admin edit form
        su_password = str(uuid.uuid4())
        superuser = User.objects.create_superuser(username='admin',
            password=su_password, email='su@example.com')

        # login as admin user
        self.client.login(username=superuser.username, password=su_password)

        # create two people and a relationship
        Person.objects.create(name='Charles Dufour', slug='dufour-charles')
        Person.objects.create(name='Dufour', title='Mlle', slug='dufour')

        # get the list url with logged in user
        person_list_url = reverse('admin:people_person_changelist')
        result = self.client.get(person_list_url)

        self.assertContains(result, Person.address_count.short_description,
            msg_prefix='should have address_count field and short_desc.')
        self.assertContains(result, Person.list_nationalities.short_description,
            msg_prefix='should have list_nationalities field and short desc.')

    def test_person_merge(self):
        # TODO: permissions required (add permission check, test)

        # get without logging in should fail
        response = self.client.get(reverse('people:merge'))
        # default django behavior is redirect to admin login page
        assert response.status_code == 302

        staff_password = str(uuid.uuid4())
        staffuser = User.objects.create_user(username='staff',
            password=staff_password, email='staff@example.com',
            is_staff=True)

        # login as staff user with no special permissions
        self.client.login(username=staffuser.username, password=staff_password)
        # staff user without persion permission should still fail
        response = self.client.get(reverse('people:merge'))
        assert response.status_code == 302

        # give staff user required permissions for merge person view
        perms = Permission.objects.filter(codename__in=['change_person', 'delete_person'])
        staffuser.user_permissions.set(list(perms))

        # create test person records to merge
        pers = Person.objects.create(name='M. Jones', slug='jones-m')
        pers2 = Person.objects.create(name='Mike Jones', slug='jones-mike')

        person_ids = [pers.id, pers2.id]
        idstring = ','.join(str(pid) for pid in person_ids)

        # GET should display choices
        response = self.client.get(reverse('people:merge'), {'ids': idstring})
        assert response.status_code == 200
        # sanity check form and display (components tested elsewhere)
        assert isinstance(response.context['form'], PersonMergeForm)
        template_names = [tpl.name for tpl in response.templates]
        assert 'people/merge_person.html' in template_names
        self.assertContains(response, pers.name)
        self.assertContains(response, pers2.name)

        # add accounts and events
        acct = Account.objects.create()
        acct.persons.add(pers)
        acct2 = Account.objects.create()
        acct2.persons.add(pers2)
        Subscription.objects.create(account=acct2)

        # add creator relationships to works
        book1 = Work.objects.create()
        book2 = Work.objects.create()
        author = CreatorType.objects.get(name='Author')
        editor = CreatorType.objects.get(name='Editor')
        Creator.objects.create(creator_type=author, person=pers, work=book1) # pers author of book1
        Creator.objects.create(creator_type=editor, person=pers2, work=book2) # pers2 editor of book2
        Creator.objects.create(creator_type=author, person=pers2, work=book2) # pers2 author of book2

        # GET should include account info
        response = self.client.get(reverse('people:merge'), {'ids': idstring})
        # account should be displayed with link to admin edit page
        self.assertContains(response, str(acct))
        self.assertContains(response, str(acct2))
        self.assertContains(
            response, reverse('admin:accounts_account_change', args=[acct.id]))
        self.assertContains(
            response, reverse('admin:accounts_account_change', args=[acct2.id]))
        # should indicate if account has no events and no card
        self.assertContains(response, 'No account events')
        self.assertContains(response, 'No associated lending library card')

        # POST should execute the merge
        response = self.client.post('%s?ids=%s' % \
                                    (reverse('people:merge'), idstring),
                                    {'primary_person': pers.id},
                                    follow=True)
        message = list(response.context.get('messages'))[0]
        assert message.tags == 'success'
        assert 'Reassociated 1 event ' in message.message
        assert 'Reassociated 2 creator roles ' in message.message
        assert pers.name in message.message
        assert str(acct) in message.message
        assert reverse('admin:people_person_change', args=[pers.id]) \
            in message.message
        assert reverse('admin:accounts_account_change', args=[acct.id]) \
            in message.message
        # confirm merge completed by checking objects were removed
        assert not Account.objects.filter(id=acct2.id).exists()
        assert not Person.objects.filter(id=pers2.id).exists()
        # check new creator relationships
        assert pers in book1.authors
        assert pers in book2.authors
        assert pers in book2.editors
        assert not pers2 in book1.authors
        assert not pers2 in book2.authors
        assert not pers2 in book2.editors

        # Test merge for people with no accounts
        pers3 = Person.objects.create(name='M. Mulshine', slug='mulshine')
        pers4 = Person.objects.create(name='Mike Mulshine', slug='mulshine-m')
        person_ids = [pers3.id, pers4.id]
        idstring = ','.join(str(pid) for pid in person_ids)

        # GET should still work
        response = self.client.get(reverse('people:merge'), {'ids': idstring})
        assert response.status_code == 200
        assert isinstance(response.context['form'], PersonMergeForm)
        template_names = [tpl.name for tpl in response.templates]
        assert 'people/merge_person.html' in template_names
        self.assertContains(response, pers3.name)
        self.assertContains(response, pers4.name)

        # POST merge should work & report no accounts changed
        response = self.client.post('%s?ids=%s' %
                                    (reverse('people:merge'), idstring),
                                    {'primary_person': pers3.id},
                                    follow=True)
        message = list(response.context.get('messages'))[0]
        assert message.tags == 'success'
        assert 'No accounts to reassociate' in message.message
        assert pers3.name in message.message
        assert reverse('admin:people_person_change', args=[pers3.id]) \
            in message.message
        assert not Person.objects.filter(id=pers4.id).exists()

        # Merging with shared account should fail
        mike = Person.objects.create(name='Mike Mulshine', slug='mulshine-2')
        spencer = Person.objects.create(name='Spencer Hadley', slug='hadley')
        nikitas = Person.objects.create(name='Nikitas Tampakis', slug='tampa')
        shared_acct = Account.objects.create()
        shared_acct.persons.add(mike)
        shared_acct.persons.add(spencer)
        idstring = ','.join(str(pid) for pid in [mike.id, spencer.id, nikitas.id])
        response = self.client.post('%s?ids=%s' %
                                    (reverse('people:merge'), idstring),
                                    {'primary_person': mike.id},
                                    follow=True)
        message = list(response.context.get('messages'))[0]
        assert message.tags == 'error'
        assert 'shared account' in message.message


class TestGeonamesLookup(TestCase):

    def test_geonames_get_label(self):
        geo_lookup = GeoNamesLookup()
        work = {'name': 'New York City', 'countryName': 'USA'}
        # country code used if available
        assert geo_lookup.get_label(work) == 'New York City, USA'
        del work['countryName']
        # and just name, if no country is available
        assert geo_lookup.get_label(work) == 'New York City'


class TestGeonamesLookupWidget(TestCase):

    def test_render(self):
        widget = GeoNamesLookupWidget()
        # no value set - should not error
        rendered = widget.render('place', None, {'id': 'place'})
        assert '<p><a id="geonames_uri" target="_blank" href=""></a></p>' \
            in rendered
        # uri value set - should be included in generated link
        uri = 'http://sws.geonames.org/2759794/'
        rendered = widget.render('place', uri, {'id': 'place'})
        assert '<a id="geonames_uri" target="_blank" href="%(uri)s">%(uri)s</a>' \
            % {'uri': uri} in rendered
        # value should be set as an option to preserve existing
        # value when the form is submitted
        assert '<option value="%(uri)s" selected>%(uri)s</option' % \
            {'uri': uri} in rendered


class TestMapWidget(TestCase):

    def test_render(self):
        widget = MapWidget()
        # no value set - should not error
        rendered = widget.render('place', None, {'id': 'place'})
        assert '<div id="geonames_map"></div>' in rendered


class TestCountryAutocompleteView(TestCase):

    def test_get_queryset(self):
        # make two countries
        Country.objects.create(name='Spain', code='ES', geonames_id='001')
        Country.objects.create(name='France', code='FR', geonames_id='002')

        # send a request, test view and queryset indirectly
        auto_url = reverse('people:country-autocomplete')
        res = self.client.get(auto_url, {'q': 'Spa'})
        assert res
        info = res.json()
        assert info['results']
        assert info['results'][0]['text'] == 'Spain'

        res = self.client.get(auto_url, {'q': 'Fra'})
        assert res
        info = res.json()
        assert info['results']
        assert info['results'][0]['text'] == 'France'


class TestLocationAutocompleteView(TestCase):

    def test_get_queryset(self):
        # make two countries
        es = Country.objects.create(name='Spain', code='ES', geonames_id='001')
        fr = Country.objects.create(name='France', code='FR', geonames_id='002')

        # make two addresses
        add_dict = {
            'name': 'Hotel Le Foo',
            'street_address': 'Rue Le Bar',
            'city': 'Paris',
            'postal_code': '012345',
            'country': fr,
        }
        add_dict2 = {
            'name': 'Hotel El Foo',
            'street_address': 'Calle El Bar',
            'city': 'Madrid',
            'postal_code': '678910',
            'country': es,
        }
        add1 = Location.objects.create(**add_dict)
        Location.objects.create(**add_dict2)

        # make a person
        person = Person.objects.create(
            name='Baz', title='Mr.', sort_name='Baz', slug='baz')

        # - series of tests for get_queryset Q's and view rendering
        # autocomplete that should get both
        auto_url = reverse('people:location-autocomplete')
        res = self.client.get(auto_url, {'q': 'Foo'})
        info = res.json()
        assert len(info['results']) == 2

        # auto complete that should get Le Foo
        res = self.client.get(auto_url, {'q': 'Rue le Bar'})
        info = res.json()
        assert len(info['results']) == 1
        assert 'Hotel Le Foo' in info['results'][0]['text']

        # auto complete that should get Le Foo
        res = self.client.get(auto_url, {'q': 'Fra'})
        info = res.json()
        assert len(info['results']) == 1
        assert 'Hotel Le Foo' in info['results'][0]['text']

        # auto complete that should get El Foo
        res = self.client.get(auto_url, {'q': '67891'})
        info = res.json()
        assert len(info['results']) == 1
        assert 'Hotel El Foo' in info['results'][0]['text']

        # auto complete that should get El Foo
        res = self.client.get(auto_url, {'q': 'Mad'})
        info = res.json()
        assert len(info['results']) == 1
        assert 'Hotel El Foo' in info['results'][0]['text']

        # autocomplete that should also find location by associated person
        Address.objects.create(location=add1, person=person)
        res = self.client.get(auto_url, {'q': 'Baz'})
        info = res.json()
        assert len(info['results']) == 1
        assert 'Hotel Le Foo' in info['results'][0]['text']


class TestPersonMergeView(TestCase):

    def test_get_success_url(self):
        person_merge = PersonMerge()
        # unset session variable should be passed as an empty string
        person_merge.request = Mock()
        person_merge.request.session = {}
        resolved_url = resolve(person_merge.get_success_url())
        assert 'admin' in resolved_url.app_names
        assert resolved_url.url_name == 'people_person_changelist'
        # test that session containing a urlencoded url is correctly
        # appended and keys that are not the one we're looking for are ignored
        person_merge.request.session = {
            'someotherkeystill': 'secretsessionvalue',
            'people_merge_filter': 'p=2&q=foo',
            'otherkey': 'ignored',
        }
        url = person_merge.get_success_url()
        assert url.endswith('?p=2&q=foo')
        # without the query string, the url should still resolve
        # to people_person_changelist
        resolved_url = resolve(url.split('?')[0])
        assert 'admin' in resolved_url.app_names
        assert resolved_url.url_name == 'people_person_changelist'

    def test_get_initial(self):
        pmview = PersonMerge()
        pmview.request = Mock(GET={'ids': '12,23,456,7'})

        initial = pmview.get_initial()
        assert pmview.person_ids == [12, 23, 456, 7]
        # lowest id selected as default primary person
        assert initial['primary_person'] == 7

    def test_get_form_kwargs(self):
        pmview = PersonMerge()
        pmview.request = Mock(GET={'ids': '12,23,456,7'})
        form_kwargs = pmview.get_form_kwargs()
        assert form_kwargs['person_ids'] == pmview.person_ids

    # form_valid method tested through client post request above


class TestMembersListView(TestCase):
    fixtures = ['sample_people.json']

    def setUp(self):
        self.factory = RequestFactory()
        self.members_url = reverse('people:members-list')

    def test_list(self):
        # test listview functionality using testclient & response

        # fixture doesn't include any cards or events,
        # so add some before indexing in Solr
        card_member = Person.objects.filter(account__isnull=False).first()
        account = card_member.account_set.first()
        Subscription.objects.create(
            account=account, start_date=date(1942, 3, 4))
        Subscription.objects.create(
            account=account, end_date=date(1950, 1, 1))

        # create card and add to account
        src_type = SourceType.objects.get_or_create(
            name='Lending Library Card')[0]
        card = Bibliography.objects.create(bibliographic_note='A Library Card',
                                           source_type=src_type)
        account.card = card
        account.save()
        Person.index_items(Person.objects.all())
        time.sleep(1)

        response = self.client.get(self.members_url)

        # filter form should be displayed with filled-in query field one time
        self.assertContains(response, 'Search member', count=1)
        # + card filter with a card count (1)
        # + counts for nationality filter (2)
        # + counts for arrondissement filter (1)
        self.assertContains(response, '<span class="count">1</span>', count=4)
        # the filter should have a card image (counted later with other result
        # card icon) and it should have a tooltip
        # total 2 tooltips on page since gender facet will also have one
        self.assertContains(response, 'role="tooltip"', count=2)
        # the tooltip should have an aria-label set
        self.assertContains(response, 'aria-label="Limit to members', count=1)
        # the input should be aria-describedby the tooltip
        self.assertContains(response, 'aria-describedby="has_card_tip"')

        # should display all library members in the database
        members = Person.objects.filter(account__isnull=False)

        assert response.context['members'].count() == members.count()
        self.assertContains(response, '%d total results' % members.count())
        for person in members:
            self.assertContains(response, person.sort_name)
            self.assertContains(response, person.birth_year)
            self.assertContains(response, person.death_year)
            # should link to person detail page
            self.assertContains(response, person.get_absolute_url())

        # only card member has account dates and card
        self.assertContains(response, account.earliest_date().year)
        self.assertContains(response, account.last_date().year)

        # should not display relevance score
        self.assertNotContains(response, '<dt>relevance</dt>')

        # hidden text for 'has card' icon should be rendered
        self.assertContains(response, 'member has card')

        # pagination options set in context
        assert response.context['page_labels']
        # current fixture is not enough to paginate
        # next/prev links should have aria-hidden to indicate not usable
        self.assertContains(response, '<a rel="prev" aria-hidden')
        self.assertContains(response, '<a rel="next" aria-hidden')
        # pagination labels are used, current page selected
        self.assertContains(
            response,
            '<option value="1" selected="selected">%s</option>' % \
            list(response.context['page_labels'])[0][1])

        # sanity check keyword search against solr
        # search for member by name; should only get one member back
        response = self.client.get(self.members_url, {'query': card_member.name})
        assert response.context['members'].count() == 1
        # should not display relevance score
        # NOTE disabled because user will be logged in to avoid 404, so
        # relevance will display
        # self.assertNotContains(response, '<dt>relevance</dt>',
        #     msg_prefix='relevance score not displayed to anonymous user')

        # sanity check date filters -- exclude the member with events
        response = self.client.get(self.members_url, {'membership_dates_0': 1951})
        assert response.context['members'].count() == 0
        # now include the member
        response = self.client.get(self.members_url, {'membership_dates_0': 1948})
        assert response.context['members'].count() == 1

        # sanity check birth year filter -- exclude active member
        response = self.client.get(self.members_url, {'birth_year_0': 1952})
        assert response.context['members'].count() == 0
        # now include members with accounts whose birthdates fall after 1882
        response = self.client.get(self.members_url, {'birth_year_0': 1882})
        assert response.context['members'].count() == 2

        # check for max, min and placeholders for date ranges
        # 1942 and 1950 should be the respective values
        self.assertContains(
            response, 'placeholder="1950"',
            msg_prefix='Membership widget sets placeholder for max year.'
        )
        self.assertContains(
            response, 'placeholder="1942"',
            msg_prefix='Membership widget sets placeholder for min year.',
        )

        # There should be two min/max, one for each input
        self.assertContains(
            response, 'max="1950"', count=2,
            msg_prefix='Response has max set twice for inputs'
        )
        self.assertContains(
            response, 'min="1942"', count=2,
            msg_prefix='Response has min set twice for inputs'
        )

        # check for max, min and placeholders for birth year
        # should be 1885 and 1899 respectively
        self.assertContains(
            response, 'placeholder="1885"',
            msg_prefix='Membership widget sets placeholder for max year.'
        )
        self.assertContains(
            response, 'placeholder="1899"',
            msg_prefix='Membership widget sets placeholder for min year.',
        )
        # There should be two min/max, one for each input
        self.assertContains(
            response, 'max="1899"', count=2,
            msg_prefix='Response has max set twice for inputs'
        )
        self.assertContains(
            response, 'min="1885"', count=2,
            msg_prefix='Response has min set twice for inputs'
        )
        # login as staff user with no special permissions
        staff_password = str(uuid.uuid4())
        staffuser = User.objects.create_user(
            username='staff', is_staff=True,
            password=staff_password, email='staff@example.com')
        self.client.login(username=staffuser.username, password=staff_password)
        response = self.client.get(self.members_url, {'query': card_member.name})
        self.assertContains(
            response, '<dt>relevance</dt>',
            msg_prefix='relevance score displayed for logged in users')

        # TODO: not sure how to test pagination/multiple pages

        # test partial match
        response = self.client.get(self.members_url, {'query': "heming"})
        self.assertContains(response, "Hemingway, Ernest")

        # test accent folding
        rene_account = Account.objects.create()
        rene = Person.objects.create(sort_name='Chambrillac, René', slug='ren')
        rene_account.persons.add(rene)
        Person.index_items([rene])
        time.sleep(1)
        # with accent
        response = self.client.get(self.members_url, {'query': "rené"})
        self.assertContains(response, rene.sort_name)
        # without accent
        response = self.client.get(self.members_url, {'query': "rene"})
        self.assertContains(response, rene.sort_name)

    def test_get_page_labels(self):
        view = MembersList()
        # patch out get_form
        view.get_year_range = Mock()
        view.get_year_range.return_value = (1900, 1930)
        view.request = self.factory.get(self.members_url)
        # trigger form valid check to ensure cleaned data is available
        view.get_form().is_valid()
        view.queryset = Mock()
        with patch('mep.people.views.alpha_pagelabels') as mock_alpha_pglabels:
            works = range(101)
            paginator = Paginator(works, per_page=50)
            result = view.get_page_labels(paginator)
            view.queryset.only.assert_called_with('sort_name')
            alpha_pagelabels_args = mock_alpha_pglabels.call_args[0]
            # first arg is paginator
            assert alpha_pagelabels_args[0] == paginator
            # second arg is queryset with revised field list
            assert alpha_pagelabels_args[1] == \
                view.queryset.only.return_value.get_results.return_value
            # third arg is a lambda
            assert isinstance(alpha_pagelabels_args[2], LambdaType)

            mock_alpha_pglabels.return_value.items.assert_called_with()
            assert result == mock_alpha_pglabels.return_value.items.return_value

            # when sorting by relevance, use numeric page labels instead
            mock_alpha_pglabels.reset_mock()
            view.request = self.factory.get(self.members_url, {'query': 'foo'})
            del view._form
            # trigger form valid check to ensure cleaned data is available
            view.get_form().is_valid()
            result = view.get_page_labels(paginator)
            mock_alpha_pglabels.assert_not_called()

    @patch('mep.people.views.super')
    def test_get_form(self, mocksuper):
        # mock out super to subsitute a mock for the actual form
        mockform = Mock()
        mocksuper.return_value.get_form.return_value = mockform
        view = MembersList()
        view.request = self.factory.get(self.members_url)
        view.get_year_ranges = Mock()

        # pass a min and max year
        view.get_year_ranges.return_value = {
            'birth_year': (1900, 1920)
        }
        view.get_form()
        # cached form is set
        assert view._form == mockform

        # form should be cached
        mockform.reset_mock()
        view.get_form()
        assert not mockform.called

    def test_get_form_kwargs(self):
        view = MembersList()
        view.get_range_stats = Mock()
        # no query args
        view.request = self.factory.get(self.members_url)
        form_kwargs = view.get_form_kwargs()
        # form initial data copied from view
        assert form_kwargs['initial'] == view.initial
        # mock ranges should be called and its value assigned to
        # kwargs
        assert form_kwargs['range_minmax'] == view.get_range_stats.return_value

        # no query, use default sort
        assert form_kwargs['data']['sort'] == view.initial['sort']

        # blank query, use default sort
        view.request = self.factory.get(self.members_url, {'query': ''})
        form_kwargs = view.get_form_kwargs()
        # no query, use default sort
        assert form_kwargs['data']['sort'] == view.initial['sort']

        # with keyword query, should default to relevance sort
        view.request = self.factory.get(self.members_url, {'query': 'stein'})
        form_kwargs = view.get_form_kwargs()
        assert form_kwargs['data']['sort'] == 'relevance'

        # with query param present but empty, use default sort
        view.request = self.factory.get(self.members_url, {'query': ''})
        form_kwargs = view.get_form_kwargs()
        assert form_kwargs['data']['sort'] == view.initial['sort']

    @patch('mep.people.views.PersonSolrQuerySet')
    def test_get_queryset(self, mock_solrqueryset):
        mock_qs = mock_solrqueryset.return_value
        # simulate fluent interface
        for meth in ['facet_field', 'filter', 'only', 'search', 'also',
                     'raw_query_parameters', 'order_by']:
            getattr(mock_qs, meth).return_value = mock_qs

        view = MembersList()
        view.request = self.factory.get(self.members_url)
        sqs = view.get_queryset()
        # queryset should be set on the view
        assert view.queryset == sqs
        mock_solrqueryset.assert_called_with()
        # inspect solr queryset filters called; should be only called once
        # because card filtering is not on
        # faceting should be turned on via call to facet_fields twice
        mock_qs.facet_field.assert_any_call('has_card')
        mock_qs.facet_field.assert_any_call(
            'gender', missing=True, exclude='gender')
        mock_qs.facet_field.assert_any_call(
            'nationality', exclude='nationality', sort='value')
        mock_qs.facet_field.assert_any_call(
            'arrondissement', exclude='arrondissement', sort='value')
        # search and raw query not called without keyword search term
        mock_qs.search.assert_not_called()
        mock_qs.raw_query_parameters.assert_not_called()
        # should sort by solr field corresponding to default sort
        mock_qs.order_by.assert_called_with(
            view.solr_sort[view.initial['sort']])

        # enable card and gender filter, also test that a blank query doesn't
        # force relevance
        view.request = self.factory.get(self.members_url, {
            'has_card': True,
            'query': '',
            'gender': ['Female', '']
        })
        # remove cached form
        del view._form
        sqs = view.get_queryset()
        assert view.queryset == sqs
        # blank query left default sort in place too
        mock_qs.order_by.assert_called_with(
            view.solr_sort[view.initial['sort']])
        # faceting should be on for both fields
        # and filtering by has card and gender, which should be tagged for
        # exclusion in calculating facets
        mock_qs.facet_field.assert_any_call('has_card')
        mock_qs.facet_field.assert_any_call('gender', missing=True, exclude='gender')
        mock_qs.filter.assert_any_call(has_card=True)
        mock_qs.filter.assert_any_call(gender__in=['Female', ''], tag='gender')

        # with keyword search term - should call search and query param
        query_term = 'sylvia'
        view.request = self.factory.get(self.members_url, {'query': query_term})
        # remove cached form
        del view._form
        sqs = view.get_queryset()
        mock_qs.search.assert_called_with(view.search_name_query)
        mock_qs.raw_query_parameters.assert_called_with(name_query=query_term)
        mock_qs.order_by.assert_called_with(view.solr_sort['relevance'])
        # include relevance score in return
        mock_qs.also.assert_called_with('score')

        # with date range
        view.request = self.factory.get(self.members_url, {'membership_dates_0': 1930})
        # remove cached form
        del view._form
        sqs = view.get_queryset()
        mock_qs.filter.assert_any_call(account_years__range=(1930, None))

        view.request = self.factory.get(
            self.members_url,
            {'membership_dates_0': 1919, 'membership_dates_1': 1923})
        del view._form
        sqs = view.get_queryset()
        mock_qs.filter.assert_any_call(account_years__range=(1919, 1923))

        # filter on nationality
        view.request = self.factory.get(self.members_url, {
            'query': '',
            'nationality': ['France']
        })
        del view._form
        sqs = view.get_queryset()
        mock_qs.filter.assert_any_call(nationality__in=['"France"'],
                                       tag='nationality')

        # filter on arrondissement
        view.request = self.factory.get(self.members_url, {
            'query': '',
            'arrondissement': ['6th']
        })
        del view._form
        sqs = view.get_queryset()
        mock_qs.filter.assert_any_call(arrondissement__in=['6'],
                                       tag='arrondissement')

    def test_invalid_form(self):
        # make an invalid range request
        view = MembersList()
        view.get_year_range = Mock()
        view.get_year_range.return_value = (1900, 1930)
        view.request = self.factory.get(self.members_url, {
            'membership_dates_0': '1930',
            'membership_dates_1': '1900', # comes before start
        })
        # should be empty SolrQuerySet
        sqs = view.get_queryset()
        assert sqs.count() == 0
        # page labels should be 'N/A'
        labels = view.get_page_labels(None) # empty paginator
        assert labels == [(1, 'N/A')]

    @patch('mep.people.views.PersonSolrQuerySet')
    def test_get_range_stats(self, mockPSQ):
        # NOTE: This depends on configuration for mapping the fields
        # in the range_field_map class attribute of MembersList
        mock_stats = {
            'stats_fields': {
                'account_years': {
                    'min': 1928.0,
                    'max': 1940.0
                },
                'birth_year': {
                    'min': 1910.0,
                    'max': 1932.0
                }
            }
        }
        mockPSQ.return_value.stats.return_value.get_stats.return_value \
            = mock_stats
        range_minmax = MembersList().get_range_stats()
        # returns integer years
        # also converst membership_dates to
        assert range_minmax == {
            'membership_dates': (1928, 1940),
            'birth_year': (1910, 1932)
        }
        # call for the correct field in stats
        args, kwargs = mockPSQ.return_value.stats.call_args_list[0]
        assert 'account_years' in args
        assert 'birth_year' in args
        # if get stats returns None, should return an empty dict
        mockPSQ.return_value.stats.return_value.get_stats.return_value = None
        assert MembersList().get_range_stats() == {}
        # None set for min or max should result in the field not being
        # returned (but the other should be passed through as expected)
        mockPSQ.return_value.stats.return_value.get_stats.return_value\
            = mock_stats
        mock_stats['stats_fields']['account_years']['min'] = None
        assert MembersList().get_range_stats() == {'birth_year': (1910, 1932)}


class TestMemberDetailView(TestCase):
    fixtures = ['sample_people.json']

    def test_get_member(self):
        gay = Person.objects.get(name='Francisque Gay', slug='gay')
        url = reverse('people:member-detail', kwargs={'slug': gay.slug})
        # create some events to check the account event date display
        account = gay.account_set.first()
        account.add_event('borrow', start_date=date(1934, 3, 4))
        account.add_event('borrow', start_date=date(1941, 2, 3))
        response = self.client.get(url)
        # check correct templates used & context passed
        self.assertTemplateUsed('member_detail.html')
        assert response.status_code == 200, \
            'library members should have a detail page'
        assert response.context['member'] == gay, \
            'page should correspond to the correct member'
        # check dates
        self.assertContains(response, '1885 – <span class="sr-only">to</span>1963', html=True)
        # check membership dates
        self.assertContains(
            response,
            'March 4, 1934 – <span class="sr-only">to</span>Feb. 3, 1941',
            html=True)
        # check VIAF
        self.assertContains(response, 'http://viaf.org/viaf/9857613')
        # check nationalities
        self.assertContains(response, 'France')
        # NOTE currently not including/checking profession

    def test_member_map(self):
        gay = Person.objects.get(name='Francisque Gay', slug='gay')
        url = reverse('people:member-detail', kwargs={'slug': gay.slug})
        response = self.client.get(url)
        # check that member map snippet is rendered since Gay has an address
        self.assertTemplateUsed('member_map.html')
        # map configs should be in context
        assert 'mapbox_token' in response.context
        assert 'mapbox_basemap' in response.context
        assert 'paris_overlay' in response.context
        # address of the library itself should be in context
        assert response.context['library_address']['name'] == 'Shakespeare & Company'
        # Gay's address info should be in context
        assert response.context['addresses'][0]['street_address'] == '3 Rue Garancière'
        assert response.context['addresses'][0]['latitude'] == '48.85101'
        assert response.context['addresses'][0]['longitude'] == '2.33590'

    def test_get_non_member(self):
        aeschylus = Person.objects.get(name='Aeschylus', slug='aeschylus')
        url = reverse('people:member-detail', kwargs={'slug': aeschylus.slug})
        response = self.client.get(url)
        assert response.status_code == 404, \
            'non-members should not have a detail page'


class TestMembershipActivities(TestCase):
    fixtures = ['sample_people.json']
    # NOTE: might want an event fixture for testing at some point

    def setUp(self):
        self.member = Person.objects.get(slug="hemingway")
        self.view = MembershipActivities()
        self.view.kwargs = {'slug': self.member.slug}

        # create account with test events
        acct = Account.objects.create()
        acct.persons.add(self.member)
        subtype = SubscriptionType.objects.create(name='Std')
        # create one event of each type to test with
        self.events = {
            'subscription': Subscription.objects.create(
                account=acct, category=subtype, start_date=date(1920, 3, 1),
                end_date=date(1920, 4, 1), price_paid=30,
                currency='FRF'),
            'reimbursement': Reimbursement.objects.create(
                account=acct, start_date=date(1920, 5, 5),
                end_date=date(1920, 5, 5), refund=15, currency='USD'),
            'generic': Event.objects.create(account=acct)
        }

    def test_get_queryset(self):
        events = self.view.get_queryset()
        # should have two events
        assert events.count() == 2
        # should return teh event object
        assert self.events['subscription'].event_ptr in events
        assert self.events['reimbursement'].event_ptr in events

    def test_get_context_data(self):
        # get queryset must be run first to populate object_list
        self.view.object_list = self.view.get_queryset()
        context = self.view.get_context_data()
        # library member set in context
        assert context['member'] == self.member
        # set on the view
        assert self.view.member == self.member

        # non-member should 404 - try author from fixture
        self.view.kwargs['slug'] = 'aeschylus'
        self.view.object_list = self.view.get_queryset()
        with pytest.raises(Http404):
            self.view.get_context_data()

    def test_get_absolute_url(self):
        assert self.view.get_absolute_url() == \
            absolutize_url(reverse('people:membership-activities',
                                   kwargs={'slug': self.member.slug}))

    def test_get_breadcrumbs(self):
        self.view.object_list = self.view.get_queryset()
        self.view.get_context_data()
        self.view.member = self.member
        crumbs = self.view.get_breadcrumbs()
        assert crumbs[0][0] == 'Home'
        # last item is this page
        assert crumbs[-1][0] == 'Membership'
        assert crumbs[-1][1] == self.view.get_absolute_url()
        # second to last is member page
        assert crumbs[-2][0] == self.member.short_name
        assert crumbs[-2][1] == absolutize_url(self.member.get_absolute_url())

    def test_view_template(self):
        response = self.client.get(reverse('people:membership-activities',
                                   kwargs={'slug': self.member.slug}))
        # table headers
        self.assertContains(response, 'Activity')
        self.assertContains(response, 'Plan')
        self.assertContains(response, 'Duration')
        self.assertContains(response, 'Start Date')
        self.assertContains(response, 'End Date')
        self.assertContains(response, 'Amount')
        # event details
        subs = self.events['subscription']
        self.assertContains(response, 'Subscription')
        self.assertContains(response, str(subs.category))
        self.assertContains(response, subs.readable_duration())
        # NOTE: can't currently duplicate the django date format used in the
        # template (and it might not be exactly what we want, either)
        # self.assertContains(response, subs.start_date.strftime('%b %d, %Y'))
        self.assertContains(
            response, 'data-sort="%s"' % subs.partial_start_date)
        self.assertContains(
            response, 'data-sort="%s"' % subs.partial_end_date)
        self.assertContains(response, subs.price_paid)
        self.assertContains(response, subs.currency_symbol())
        self.assertContains(response, 'Reimbursement')
        reimburse = self.events['reimbursement']
        # start/end should be same sort value stwice
        self.assertContains(
            response, 'data-sort="%s"' %
            reimburse.partial_start_date,
            count=2)
        self.assertContains(response, '-%d' % reimburse.refund)
        self.assertContains(response, reimburse.currency_symbol())

        # test member with no membership activity
        response = self.client.get(reverse('people:membership-activities',
                                   kwargs={'slug': 'gay'}))
        self.assertNotContains(response, '<table')
        self.assertContains(response, 'No documented membership activity')


class TestBorrowingActivities(TestCase):
    fixtures = ['sample_people.json']
    # NOTE: might want an event fixture for testing at some point

    def setUp(self):
        self.member = Person.objects.get(slug="hemingway")
        self.view = BorrowingActivities()
        self.view.kwargs = {'slug': self.member.slug}

        # create account with test events and test works
        acct = Account.objects.create()
        acct.persons.add(self.member)
        maidens = Work.objects.get(title='Suppliant Maidens')
        awakening = Work.objects.get(title='The Awakening of Helena Richie')
        rises = Work.objects.get(title='The Sun Also Rises')

        # create one event of each type to test with
        self.events = {
            'borrow': Borrow.objects.create(account=acct, work=maidens,
                start_date=date(1924, 2, 1),
                end_date=date(1924, 3, 1),
                start_date_precision=(DatePrecision.year | DatePrecision.month),
                end_date_precision=(DatePrecision.year | DatePrecision.month),
            ),
            'purchase': Purchase.objects.create(account=acct, work=awakening,
                start_date=date(1900, 11, 27),
                start_date_precision=(DatePrecision.month | DatePrecision.day),
            ),
            'generic': Event.objects.create(account=acct, work=rises,
                start_date=date(1922, 6, 3),
            )
        }

        # set partial dates
        self.events['borrow'].partial_start_date = '1924-02'
        self.events['borrow'].partial_end_date = '1924-03'

    def test_get_queryset(self):
        events = self.view.get_queryset()
        # should have three events
        assert events.count() == 3
        # should return teh event object
        assert self.events['borrow'].event_ptr in events
        assert self.events['purchase'].event_ptr in events

    def test_get_context_data(self):
        # get queryset must be run first to populate object_list
        self.view.object_list = self.view.get_queryset()
        context = self.view.get_context_data()
        # library member set in context
        assert context['member'] == self.member
        # set on the view
        assert self.view.member == self.member

        # non-member should 404 - try author from fixture
        self.view.kwargs['slug'] = 'aeschylus'
        self.view.object_list = self.view.get_queryset()
        with pytest.raises(Http404):
            self.view.get_context_data()

    def test_get_absolute_url(self):
        assert self.view.get_absolute_url() == \
            absolutize_url(reverse('people:borrowing-activities',
                                   kwargs={'slug': self.member.slug}))

    def test_get_breadcrumbs(self):
        self.view.object_list = self.view.get_queryset()
        self.view.get_context_data()
        self.view.member = self.member
        crumbs = self.view.get_breadcrumbs()
        assert crumbs[0][0] == 'Home'
        # last item is this page
        assert crumbs[-1][0] == 'Borrowing'
        assert crumbs[-1][1] == self.view.get_absolute_url()
        # second to last is member page
        assert crumbs[-2][0] == self.member.short_name
        assert crumbs[-2][1] == absolutize_url(self.member.get_absolute_url())

    def test_view_template(self):
        response = self.client.get(reverse('people:borrowing-activities',
                                   kwargs={'slug': self.member.slug}))
        # table headers
        self.assertContains(response, 'Title')
        self.assertContains(response, 'Author')
        self.assertContains(response, 'Publication Date')
        self.assertContains(response, 'Activity')
        self.assertContains(response, 'Start Date')
        self.assertContains(response, 'End Date')

        # event details - borrow
        self.assertContains(response, 'Borrow')  # type
        self.assertContains(response, 'Suppliant Maidens')  # title
        self.assertContains(response, 'Aeschylus')  # author
        self.assertContains(response, '1922')  # pub date
        self.assertContains(response, 'Feb. 1924')  # partial start date
        self.assertContains(response, 'March 1924')  # partial end date
        self.assertContains(response, 'data-sort="1924-02"')  # sorting
        self.assertContains(response, 'data-sort="1924-03"')  # sorting

        # event details - purchase
        self.assertContains(response, 'Purchase')  # type
        self.assertContains(response, 'The Awakening of Helena Richie')  # title
        self.assertContains(response, 'Margaret Deland')  # author
        self.assertContains(response, '1906')  # pub date
        self.assertContains(response, 'Nov. 27')  # partial start date
        self.assertContains(response, 'data-sort="--11-27"')  # sorting

        # event details - generic
        self.assertContains(response, '-')  # type
        self.assertContains(response, 'The Sun Also Rises')  # title
        self.assertContains(response, 'Ernest Hemingway')  # author
        self.assertContains(response, '1926')  # pub date
        self.assertContains(response, 'June 3, 1922')  # start date
        self.assertContains(response, 'data-sort="1922-06-03"')  # sorting

        # test member with no borrowing activity
        response = self.client.get(reverse('people:borrowing-activities',
                                   kwargs={'slug': 'gay'}))
        self.assertNotContains(response, '<table')
        self.assertContains(response, 'No documented borrowing activity')


class TestMembershipGraphs(TestCase):

    @patch('mep.people.views.PersonSolrQuerySet')
    def test_get_context_data(self, mock_solrqueryset):
        mock_qs = mock_solrqueryset.return_value
        # simulate fluent interface
        for meth in ['facet_field', 'filter', 'only', 'search', 'also',
                     'raw_query_parameters', 'order_by']:
            getattr(mock_qs, meth).return_value = mock_qs

        mock_qs.get_facets.return_value = {
            'facet_fields': {
                "account_yearmonths": OrderedDict([
                    ("192601", 242),
                    ("192512", 236),
                    ("192511", 234),
                ]),
                "logbook_yearmonths": OrderedDict([
                    ("192601", 231),
                    ("192511", 225),
                    ("192512", 225),
                ]),
                "card_yearmonths": OrderedDict([
                    ("193805", 61),
                    ("194002", 57),
                    ("193806", 53),
                ])
            }
        }

        context = MembershipGraphs().get_context_data()

        assert 'data' in context
        for series in ['members', 'logbooks', 'cards']:
            assert series in context['data']

        assert context['data']['members'][0] == {
            'startDate': '1926-01-01',
            'count': 242
        }


class TestMemberCardList(TestCase):
    fixtures = ['footnotes_gstein', 'sample_people']

    def setUp(self):
        self.factory = RequestFactory()
        self.cardlist_url = reverse('people:member-card-list',
                                    kwargs={'slug': 'stein-gertrude'})
        self.view = MemberCardList()
        self.view.request = self.factory.get(self.cardlist_url)
        # simulate anonymous user
        self.view.request.user = AnonymousUser()

    def test_get_queryset(self):
        # invalid slug should result in a 404
        self.view.kwargs = {'slug': 'bogus'}
        with pytest.raises(Http404):
            self.view.get_queryset()

        self.view.kwargs = {'slug': 'stein-gertrude'}
        canvas_ids = list(self.view.get_queryset().values_list('pk', flat=True))
        # member should be stored on the view
        assert self.view.member == Person.objects.get(slug='stein-gertrude')
        # queryset should be canvas ids for footnotes associated with Stein
        assert canvas_ids == list(Footnote.objects.filter(
            bibliography__bibliographic_note__contains='Gertrude Stein'
        ).values_list('image__pk', flat=True).distinct())

    def test_get_absolute_url(self):
        self.view = MemberCardList()
        self.view.kwargs = {'slug': 'stein'}
        assert self.view.get_absolute_url() == \
            absolutize_url(reverse('people:member-card-list',
                                   kwargs=self.view.kwargs))

    def test_get_breadcrumbs(self):
        self.view.kwargs = {'slug': 'stein-gertrude'}
        # get queryset to populate member & object
        self.view.get_queryset()
        crumbs = self.view.get_breadcrumbs()
        assert crumbs[0][0] == 'Home'
        # last item is this page
        assert crumbs[-1][0] == 'Cards'
        assert crumbs[-1][1] == self.view.get_absolute_url()
        # second to last is member page
        assert crumbs[-2][0] == self.view.member.short_name
        assert crumbs[-2][1] == \
            absolutize_url(self.view.member.get_absolute_url())

    def test_get_context_data(self):
        self.view.kwargs = {'slug': 'stein-gertrude'}
        self.view.object_list = self.view.get_queryset()
        context = self.view.get_context_data()
        assert context['member'] == self.view.member

    @login_temporarily_required
    def test_view_template(self):
        member = Person.objects.get(slug='stein-gertrude')
        response = self.client.get(reverse('people:member-card-list',
                                   kwargs={'slug': 'stein-gertrude'}))
        self.assertTemplateUsed('people/member_cardlist.html')
        self.assertTemplateUsed('snippets/breadcrumbs.html')
        # first name used for page title
        self.assertContains(response, member.firstname_last)
        # links to main member page
        self.assertContains(response, member.get_absolute_url())
        cards = Canvas.objects.filter(
            manifest__bibliography__account__persons__slug=member.slug)

        for card in cards:
            # include iiif images in src (1x twice for img and source)
            self.assertContains(response, card.image.size(width=225), count=2)
            self.assertContains(response, card.image.size(width=450), count=1)
            dates = card.footnote_set.all().event_date_range()
            if dates:
                start, end = dates
                # always show start year if set
                self.assertContains(response, start.year)
                # show end year if different
                if start.year != end.year:
                    self.assertContains(response, end.year)
            else:
                self.assertContains(response, 'Unknown')

        # iiif license image, text & link
        self.assertContains(response, 'No Known Copyright')
        self.assertContains(response, 'rightsstatements_org/NKC.svg')
        # iiif logo icon
        self.assertContains(response, 'pul_logo_icon')

        # library member wih no cards
        response = self.client.get(reverse('people:member-card-list',
                                   kwargs={'slug': 'gay'}))
        self.assertContains(response, 'No lending library cards available')


class TestMemberCardDetail(TestCase):
    fixtures = ['footnotes_gstein', 'sample_people']

    # short id for first canvas in manifest for stein's card
    canvas_id = '68fd36f1-a463-441e-9f13-dfc4a6cd4114'
    kwargs = {'slug': 'stein-gertrude', 'short_id': canvas_id}

    def setUp(self):
        self.factory = RequestFactory()
        self.cardlist_url = reverse('people:member-card-detail',
                                    kwargs=self.kwargs)
        self.view = MemberCardDetail()
        self.view.request = self.factory.get(self.cardlist_url)
        # simulate anonymous user
        self.view.request.user = AnonymousUser()

    def test_get_object(self):
        # invalid member slug should result in a 404
        self.view.kwargs = {'slug': 'bogus', 'canvas_id': self.canvas_id}
        with pytest.raises(Http404):
            self.view.get_object()

        # valid member slug with invalid canvas id should result in a 404
        self.view.kwargs = self.kwargs.copy()
        self.view.kwargs['short_id'] = 'foo'
        with pytest.raises(Http404):
            self.view.get_object()

        self.view.kwargs = self.kwargs
        expected_card = Canvas.objects.get(short_id=self.canvas_id)
        card = self.view.get_object()
        assert card == expected_card
        # member should be stored on the view
        assert self.view.member == Person.objects.get(slug='stein-gertrude')
        # label should be set
        card_dates = card.footnote_set.event_date_range()
        # single-year card
        assert self.view.label == card_dates[0].year

    def test_get_absolute_url(self):
        self.view.kwargs = {'slug': 'stein', 'short_id': self.canvas_id}
        assert self.view.get_absolute_url() == \
            absolutize_url(reverse('people:member-card-detail',
                                   kwargs=self.view.kwargs))

    def test_get_breadcrumbs(self):
        self.view.kwargs = self.kwargs
        # get object to populate member, object, and label
        self.view.get_object()
        crumbs = self.view.get_breadcrumbs()
        assert crumbs[0][0] == 'Home'
        # last item is this page
        assert crumbs[-1][0] == self.view.label
        assert crumbs[-1][1] == self.view.get_absolute_url()
        # second last item is card gallery view
        assert crumbs[-2][0] == 'Cards'
        assert crumbs[-2][1] == \
            absolutize_url(reverse('people:member-card-list',
                                   kwargs={'slug': 'stein-gertrude'}))
        # third to last is member page
        assert crumbs[-3][0] == self.view.member.short_name
        assert crumbs[-3][1] == \
            absolutize_url(self.view.member.get_absolute_url())

    def test_get_context_data(self):
        self.view.kwargs = self.kwargs
        self.view.object = self.view.get_object()
        context = self.view.get_context_data()
        assert context['member'] == self.view.member
        assert context['label'] == self.view.label
        expected_events = self.view.object.footnote_set.events()
        assert context['events'].count() == expected_events.count()
        assert set(context['events'].values_list('pk', flat=True)) == \
            set(expected_events.values_list('pk', flat=True))
        # canvas 0 is no previous, 2 is next
        assert context['prev_card'] == Canvas.objects.get(order=0).short_id
        assert context['next_card'] == Canvas.objects.get(order=2).short_id

    @login_temporarily_required
    def test_view_template(self):
        member = Person.objects.get(slug='stein-gertrude')
        response = self.client.get(reverse('people:member-card-detail',
                                   kwargs=self.kwargs))
        self.assertTemplateUsed('people/member_card_detail.html')
        self.assertTemplateUsed('snippets/breadcrumbs.html')
        # first name used for page title
        self.assertContains(response, member.firstname_last)
        # links to main member page
        self.assertContains(response, member.get_absolute_url())
        card = Canvas.objects.get(short_id=self.canvas_id)

        # 1x image appears twice for image and source; 2x once only
        self.assertContains(response, card.image.size(width=430), count=2)
        self.assertContains(response, card.image.size(width=860), count=1)
        # event details displayed
        events = card.footnote_set.all().events()
        for event in events:
            self.assertContains(response, partialdate(event.partial_start_date))
            self.assertContains(response, event.work.title)
            self.assertContains(response, event.event_type)
            self.assertContains(response, partialdate(event.partial_end_date))

        # links to next/previous pages
        context = response.context
        self.assertContains(
            response,
            reverse('people:member-card-detail',
                    kwargs={'slug': context['member'].slug,
                            'short_id': context['prev_card']}))
        self.assertContains(
            response,
            reverse('people:member-card-detail',
                    kwargs={'slug': context['member'].slug,
                            'short_id': context['next_card']}))

        # iiif license image, text & link
        self.assertContains(response, 'No Known Copyright')
        self.assertContains(response, 'rightsstatements_org/NKC.svg')
        # iiif logo icon
        self.assertContains(response, 'pul_logo_icon')
