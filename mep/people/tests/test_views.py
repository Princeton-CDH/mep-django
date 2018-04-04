import json
from datetime import date
from unittest.mock import patch, Mock

from django.contrib.messages import get_messages
from django.contrib.auth.models import User, Permission
from django.http import JsonResponse
from django.template.defaultfilters import date as format_date
from django.test import TestCase
from django.urls import reverse, resolve

from mep.accounts.models import Account, Address, Event, Subscription, \
    Reimbursement
from mep.people.admin import GeoNamesLookupWidget, MapWidget
from mep.people.forms import PersonMergeForm
from mep.people.geonames import GeoNamesAPI
from mep.people.models import Location, Country, Person, Relationship, \
    RelationshipType
from mep.people.views import GeoNamesLookup, PersonMerge


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

        # POST should attempt to merge - error message should be reported
        response = self.client.post('%s?ids=%s' % \
                                    (reverse('people:merge'), idstring),
                                    {'primary_person': pers.id},
                                    follow=True)
        self.assertRedirects(response, reverse('admin:people_person_changelist'))
        message = list(response.context.get('messages'))[0]
        assert message.tags == 'error'
        assert "Can't merge with a person record that has no account." \
            == message.message

        # add accounts and events
        acct = Account.objects.create()
        acct.persons.add(pers)
        acct2 = Account.objects.create()
        acct2.persons.add(pers2)
        Subscription.objects.create(account=acct2)
        response = self.client.post('%s?ids=%s' % \
                                    (reverse('people:merge'), idstring),
                                    {'primary_person': pers.id},
                                    follow=True)
        message = list(response.context.get('messages'))[0]
        assert message.tags == 'success'
        assert 'Reassociated 1 event ' in message.message
        assert pers.name in message.message
        assert str(acct) in message.message
        assert reverse('admin:people_person_change', args=[pers.id]) \
            in message.message
        assert reverse('admin:accounts_account_change', args=[acct.id]) \
            in message.message
        # confirm merge completed by checking objects were removed
        assert not Account.objects.filter(id=acct2.id).exists()
        assert not Person.objects.filter(id=pers2.id).exists()


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
        # empty GET dictionary in request should result in the changelist url
        person_merge.request = Mock()
        person_merge.request.GET = {}
        resolved_url = resolve(person_merge.get_success_url())
        assert 'admin' in resolved_url.app_names
        assert resolved_url.url_name == 'people_person_changelist'
        # having a 'p' value in should result in a url with a query string
        # in the format ?p= to match the pagination marker on the Django admin
        person_merge.request.GET = {'p': '2', 'q': 'foo'}
        url = person_merge.get_success_url()
        assert url.endswith('?p=2')
        # without the query string, it should still resolve
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
