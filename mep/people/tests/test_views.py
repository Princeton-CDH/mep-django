import json
from datetime import date
import time
from types import LambdaType
from unittest.mock import call, patch, Mock

from django.contrib.auth.models import User, Permission
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.defaultfilters import date as format_date
from django.test import TestCase, RequestFactory
from django.urls import reverse, resolve

from mep.accounts.models import Account, Address, Event, Subscription, \
    Reimbursement
from mep.books.models import Item, CreatorType, Creator
from mep.people.admin import GeoNamesLookupWidget, MapWidget
from mep.people.forms import PersonMergeForm
from mep.people.geonames import GeoNamesAPI
from mep.people.models import Location, Country, Person, Relationship, \
    RelationshipType
from mep.people.views import GeoNamesLookup, PersonMerge, MembersList
from mep.footnotes.models import Bibliography, SourceType


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
        item = data['results'][0]
        assert item['text'] == 'New York City, USA'
        assert item['name'] == 'New York City'
        assert item['lat'] == mock_response[0]['lat']
        assert item['lng'] == mock_response[0]['lng']
        assert item['id'] == \
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
        beach = Person.objects.create(name='Sylvia Beach', mep_id='sylv.b')

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
        ms_sylvia = Person.objects.create(name='Sylvia', title='Ms.')

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
        expected = '<strong>Sylvia Beach (1900 - 1970)</strong> sylv.b <br />'
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
        expected = ('<strong>Sylvia Beach (1900 - 1970)</strong> '
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
                    'Subscription (1971-01-01 - 1971-01-31)')
        self.assertInHTML(expected, text)

    def test_person_admin_change(self):
        # create user with permission to load admin edit form
        su_password = 'itsasecret'
        superuser = User.objects.create_superuser(username='admin',
            password=su_password, email='su@example.com')

        # login as admin user
        self.client.login(username=superuser.username, password=su_password)

        # create two people and a relationship
        m_dufour = Person.objects.create(name='Charles Dufour')
        mlle_dufour = Person.objects.create(name='Dufour', title='Mlle')
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
        su_password = 'itsasecret'
        superuser = User.objects.create_superuser(username='admin',
            password=su_password, email='su@example.com')

        # login as admin user
        self.client.login(username=superuser.username, password=su_password)

        # create two people and a relationship
        Person.objects.create(name='Charles Dufour')
        Person.objects.create(name='Dufour', title='Mlle')

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

        staff_password = 'sosecret'
        staffuser = User.objects.create_user(username='staff',
            password=staff_password, email='staff@example.com',
            is_staff=True)

        # login as staff user without no special permissios
        self.client.login(username=staffuser.username, password=staff_password)
        # staff user without persion permission should still fail
        response = self.client.get(reverse('people:merge'))
        assert response.status_code == 302

        # give staff user required permissions for merge person view
        perms = Permission.objects.filter(codename__in=['change_person', 'delete_person'])
        staffuser.user_permissions.set(list(perms))

         # create test person records to merge
        pers = Person.objects.create(name='M. Jones')
        pers2 = Person.objects.create(name='Mike Jones')

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

        # add creator relationships to items
        book1 = Item.objects.create()
        book2 = Item.objects.create()
        author = CreatorType.objects.get(name='Author')
        editor = CreatorType.objects.get(name='Editor')
        Creator.objects.create(creator_type=author, person=pers, item=book1) # pers author of book1
        Creator.objects.create(creator_type=editor, person=pers2, item=book2) # pers2 editor of book2
        Creator.objects.create(creator_type=author, person=pers2, item=book2) # pers2 author of book2

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
        pers3 = Person.objects.create(name='M. Mulshine')
        pers4 = Person.objects.create(name='Mike Mulshine')
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
        response = self.client.post('%s?ids=%s' % \
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
        mike = Person.objects.create(name='Mike Mulshine')
        spencer = Person.objects.create(name='Spencer Hadley')
        nikitas = Person.objects.create(name='Nikitas Tampakis')
        shared_acct = Account.objects.create()
        shared_acct.persons.add(mike)
        shared_acct.persons.add(spencer)
        idstring = ','.join(str(pid) for pid in [mike.id, spencer.id, nikitas.id])
        response = self.client.post('%s?ids=%s' % \
                                    (reverse('people:merge'), idstring),
                                    {'primary_person': mike.id},
                                    follow=True)
        message = list(response.context.get('messages'))[0]
        assert message.tags == 'error'
        assert 'shared account' in message.message

class TestGeonamesLookup(TestCase):

    def test_geonames_get_label(self):
        geo_lookup = GeoNamesLookup()
        item = {'name': 'New York City', 'countryName': 'USA'}
        # country code used if available
        assert geo_lookup.get_label(item) == 'New York City, USA'
        del item['countryName']
        # and just name, if no country is available
        assert geo_lookup.get_label(item) == 'New York City'


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
        person = Person.objects.create(name='Baz', title='Mr.', sort_name='Baz')

        # - series of tests for get_queryset Q's and view rendering
        # autocomplete that should get both
        auto_url = reverse('people:location-autocomplete')
        res = self.client.get(auto_url, {'q': 'Foo'})
        info = res.json()
        assert len(info['results']) == 2

        # auto complete that should get Le Foo
        res = self.client.get(auto_url, {'q': 'Rue'})
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
        Subscription.objects.create(account=account, start_date=date(1942, 3, 4))
        Subscription.objects.create(account=account, end_date=date(1950, 1, 1))

        # create card and add to account
        src_type = SourceType.objects.get_or_create(name='Lending Library Card')[0]
        card = Bibliography.objects.create(bibliographic_note='A Library Card',
                                           source_type=src_type)
        account.card = card
        account.save()

        Person.index_items(Person.objects.all())
        time.sleep(1)

        response = self.client.get(self.members_url)

        # filter form should be displayed with filled-in query field one time
        self.assertContains(response, 'Search member', count=1)
        # it should also have a card filter with a card count (check via card count)
        self.assertContains(response, '<span class="count">1</span>', count=1)
        # the filter should have a card image (counted later with other result
        # card icon) and it should have a tooltip
        self.assertContains(response, 'role="tooltip"', count=1)
        # the tooltip should have an aria-label set
        self.assertContains(response, 'aria-label="This filter will narrow', count=1)
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

        # icon for 'has card' should show up twice, once in the list
        # and once in the filter icon
        self.assertContains(response, 'card icon', count=2)

        # pagination options set in context
        assert response.context['page_labels']
        # current fixture is not enough to paginate
        # next/prev links should not display at all
        self.assertNotContains(response, '<a rel="prev"')
        self.assertNotContains(response, '<a rel="next"')
        # pagination labels are used, current page selected
        self.assertContains(
            response,
            '<option value="1" selected="selected">%s</option>' % \
            list(response.context['page_labels'])[0][1])

        # sanity check keyword search against solr
        # search for member by name; should only get one member back
        response = self.client.get(self.members_url, {'query': card_member.name})
        assert response.context['members'].count() == 1

        # TODO: not sure how to test pagination/multiple pages

    def test_get_page_labels(self):
        view = MembersList()
        view.request = self.factory.get(self.members_url)
        # trigger form valid check to ensure cleaned data is available
        view.get_form().is_valid()
        view.queryset = Mock()
        with patch('mep.people.views.alpha_pagelabels') as mock_alpha_pglabels:
            items = range(101)
            paginator = Paginator(items, per_page=50)
            result = view.get_page_labels(paginator)
            view.queryset.only.assert_called_with(sort_name='sort_name_t')
            alpha_pagelabels_args = mock_alpha_pglabels.call_args[0]
            # first arg is paginator
            assert alpha_pagelabels_args[0] == paginator
            # second arg is queryset with revised field list
            assert alpha_pagelabels_args[1] == view.queryset.only.return_value
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

    def test_get_form_kwargs(self):
        view = MembersList()
        # no query args
        view.request = self.factory.get(self.members_url)
        form_kwargs = view.get_form_kwargs()
        # form initial data copied from view
        assert form_kwargs['initial'] == view.initial
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
        assert form_kwargs['data']['sort'] ==  view.initial['sort']

    @patch('mep.people.views.SolrQuerySet')
    def test_get_queryset(self, mock_solrqueryset):
        mock_qs = mock_solrqueryset.return_value
        # simulate fluent interface
        for meth in ['facet_field', 'filter', 'only', 'search',
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
        mock_qs.filter.assert_called_once_with(item_type='person')
        mock_qs.only.assert_called_with(
            name='name_t', sort_name='sort_name_t',
            birth_year='birth_year_i', death_year='death_year_i',
            account_start='account_start_i', account_end='account_end_i',
            has_card='has_card_b', pk='pk_i')
        # faceting should be turned on via call to facet
        mock_qs.facet_field.assert_has_calls([
            call('has_card_b'),
            call('sex_s', missing=True, exclude='sex')
        ])
        # search and raw query not called without keyword search term
        mock_qs.search.assert_not_called()
        mock_qs.raw_query_parameters.assert_not_called()
        # should sort by solr field corresponding to default sort
        mock_qs.order_by.assert_called_with(view.solr_sort[view.initial['sort']])

        # enable card and sex filter, also test that a blank query doesn't force relevance
        view.request = self.factory.get(self.members_url, {
            'has_card': True,
            'query': '',
            'sex': ['Female', 'Unknown']
        })
        # remove cached form
        del view._form
        sqs = view.get_queryset()
        assert view.queryset == sqs
        # blank query left default sort in place too
        mock_qs.order_by.assert_called_with(view.solr_sort[view.initial['sort']])
        # faceting should be on and filter calls for card and sex
        mock_qs.filter.assert_has_calls(
            [
                call(has_card_b=True),
                call(sex_s__in=['Female', 'Unknown'], tag='sex')
            ]
        )
        # with keyword search term - should call search and query param
        query_term = 'sylvia'
        view.request = self.factory.get(self.members_url, {'query': query_term})
        # remove cached form
        del view._form
        sqs = view.get_queryset()
        mock_qs.search.assert_called_with(view.search_name_query)
        mock_qs.raw_query_parameters.assert_called_with(name_query=query_term)
        mock_qs.order_by.assert_called_with(view.solr_sort['relevance'])


class TestMemberDetailView(TestCase):
    fixtures = ['sample_people.json']

    def test_get_member(self):
        gay = Person.objects.get(name='Francisque Gay')
        url = reverse('people:member-detail', kwargs={'pk': gay.pk})
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
        # check name
        self.assertContains(response, 'Francisque Gay')
        # check dates
        self.assertContains(response, '1885 - 1963')
        # check membership dates
        self.assertContains(response, 'Membership Dates')
        self.assertContains(response, 'March 4, 1934 - Feb. 3, 1941')
        # check VIAF
        self.assertContains(response, 'Reference')
        self.assertContains(response, 'http://viaf.org/viaf/9857613')
        # check nationalities
        self.assertContains(response, 'Nationality')
        self.assertContains(response, 'France')
        # NOTE currently not including/checking profession

    def test_get_non_member(self):
        aeschylus = Person.objects.get(name='Aeschylus')
        url = reverse('people:member-detail', kwargs={'pk': aeschylus.pk})
        response = self.client.get(url)
        assert response.status_code == 404, \
            'non-members should not have a detail page'
