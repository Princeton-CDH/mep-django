import re
from unittest.mock import patch, Mock

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, MultipleObjectsReturned, \
    ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
import pytest
from viapy.api import ViafEntity

from mep.accounts.models import Account, Subscription, Reimbursement, Address
from mep.footnotes.models import SourceType, Bibliography, Footnote
from mep.people.models import InfoURL, Person, Profession, Relationship, \
    RelationshipType, Location, Country, PersonQuerySet
from mep.people.admin import PersonAdmin


class TestPerson(TestCase):

    def test_str(self):
        # Use name if sort name is not set
        person_foo = Person(name='Foo')
        assert str(person_foo) == 'Foo'

        # Use sort name if available
        foo_bar = Person(name='Foo Bar', sort_name='Bar, Foo')
        assert str(foo_bar) == 'Bar, Foo'

        # Add title if it exists
        foo_bar = Person(name='Bar', title='Mr.')
        assert str(foo_bar) == 'Mr. Bar'

        # if last, first, title goes after
        foo_bar = Person(sort_name='Bar, Foo', title='Mr.')
        assert str(foo_bar) == 'Bar, Foo, Mr.'

        # if not last first, in front
        foo_bar = Person(sort_name='Bar', title='Mr.')
        assert str(foo_bar) == 'Mr. Bar'

    def test_repr(self):
        # Foo Bar, born 1900
        person_foo = Person(name='Foo', sort_name='Bar, Foo', birth_year=1900)
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Person {'k':v, ...}>""
        overall = re.compile(r'<Person \{.+\}>')
        assert re.search(overall, repr(person_foo))

    def test_viaf(self):
        pers = Person(name='Beach')
        assert pers.viaf is None
        pers.viaf_id = 'http://viaf.org/viaf/35247539'
        assert isinstance(pers.viaf, ViafEntity)
        assert pers.viaf.uri == pers.viaf_id

    def test_set_birth_death_years(self):
        pers = Person(name='Humperdinck')
        # no viaf id
        pers.set_birth_death_years()
        assert pers.birth_year is None
        assert pers.death_year is None

        pers.viaf_id = 'http://viaf.org/viaf/35247539'
        with patch.object(Person, 'viaf') as mockviaf_entity:
            mockviaf_entity.birthyear = 1902
            mockviaf_entity.deathyear = 1953
            pers.set_birth_death_years()
            assert pers.birth_year == mockviaf_entity.birthyear
            assert pers.death_year == mockviaf_entity.deathyear

    def test_save(self):
        pers = Person(name='Humperdinck')
        with patch.object(pers, 'set_birth_death_years') as mock_setbirthdeath:
            # no viaf - should not call set birth/death
            pers.save()
            mock_setbirthdeath.assert_not_called()

            # viaf and dates set - should not call set birth/death
            pers.viaf_id = 'http://viaf.org/viaf/35247539'
            pers.birth_year = 1801
            pers.death_year = 1850
            pers.save()
            mock_setbirthdeath.assert_not_called()

            # viaf and one date set - should not call set birth/death
            pers.birth_year = None
            pers.save()
            mock_setbirthdeath.assert_not_called()

            # viaf and one date set - *should* call set birth/death
            pers.death_year = None
            pers.save()
            mock_setbirthdeath.assert_called_with()

    def test_address_count(self):

        # create a person
        pers = Person.objects.create(name='Foobar')
        # no addresses
        assert pers.address_count() == 0
        loc = Location.objects.create(name='L\'Hotel', city='Paris')

        # add an address
        Address.objects.create(location=loc, person=pers)
        # should be one
        assert pers.address_count() == 1

        # add another, should be 2
        loc2 = Location.objects.create(name='Elysian Fields', city='Paris')
        Address.objects.create(location=loc2, person=pers)
        assert pers.address_count() == 2

    def test_nationality_list(self):
        # create a person
        pers = Person.objects.create(name='Foobar')
        # no nationalities
        assert pers.list_nationalities() == ''
        country = Country.objects.create(name='France', code='FR')
        pers.nationalities.add(country)
        assert pers.list_nationalities() == 'France'
        # add spanish citizenship
        country = Country.objects.create(name='Spain', geonames_id='123')
        pers.nationalities.add(country)
        assert pers.list_nationalities() == 'France, Spain'

    def test_has_account(self):
        # create a person
        pers = Person.objects.create(name='Foobar')
        # create an account
        acct = Account.objects.create()
        # not associated, returns False
        assert not pers.has_account()
        # associate, should return True
        acct.persons.add(pers)
        acct.save()
        assert pers.has_account()

    def test_in_logbooks(self):
        # create test person & account and associate them
        pers = Person.objects.create(name='John')
        # no account - not in logbooks
        assert not pers.in_logbooks()

        acct = Account.objects.create()
        acct.persons.add(pers)
        # account but no logbook events
        assert not pers.in_logbooks()

        # add subscription event
        subs = Subscription.objects.create(account=acct)
        assert pers.in_logbooks()

        # add reimbursment
        Reimbursement.objects.create(account=acct)
        assert pers.in_logbooks()

        # still true if only reimbursement and no subscription
        subs.delete()
        assert pers.in_logbooks()


class TestPersonQuerySet(TestCase):

    def test_merge_with(self):
        # create test records to merge
        Person.objects.bulk_create([
            Person(name='Jones'),
            Person(name='Jones', title='Mr'),
            Person(name='Jonas'),
        ])

        # use Jonas as record to merge others to
        main_person = Person.objects.get(name='Jonas')
        # person to merge with has no account - error
        with pytest.raises(ObjectDoesNotExist) as err:
            Person.objects.merge_with(main_person)
        assert "Can't merge with a person record that has no account" in \
            str(err)

        # create accounts with content to merge
        main_acct = Account.objects.create()
        main_acct.persons.add(main_person)
        Subscription.objects.create(account=main_acct)

        # account with events and addresses
        mr_jones = Person.objects.get(name='Jones', title='Mr')
        mr_jones_acct = Account.objects.create()
        mr_jones_acct.persons.add(mr_jones)
        Subscription.objects.create(account=mr_jones_acct)
        Reimbursement.objects.create(account=mr_jones_acct)
        hotel = Location.objects.create(name="La Hotel", city="Paris")
        residence = Location.objects.create(name="52 La Rue", city="Paris")
        # account address
        acct_addr = Address.objects.create(location=hotel, account=mr_jones_acct)
        # person address
        mr_jones_addr = Address.objects.create(location=residence, person=mr_jones)

        # merge everything with Jonas
        Person.objects.merge_with(main_person)
        # should delete duplicate records
        assert Person.objects.count() == 1
        # automatically excludes merge person target from merge logic,
        # even if the record is included in the queryset
        assert Person.objects.filter(id=main_person.id).exists()
        # account events should be reassociated
        main_acct.event_set.count() == 3
        # account address should be reassociated
        assert main_acct.address_set.filter(id=acct_addr.id).exists()
        # person address should be reassociated
        assert mr_jones_addr in main_person.address_set.all()
        # accounts associated with merged persons should be gone
        assert not Account.objects.filter(id=mr_jones_acct.id).exists()

        # no mepids, but should still list that the merges occurred
        # get the current date for the string - used below
        iso_date = timezone.now().strftime('%Y-%m-%d')
        assert main_person.notes
        jones_str = 'Merged Jones on %s' % iso_date
        # Jones will appear twice from being merged into Jonas
        assert main_person.notes.count(jones_str) == 2

        # error on attempt to merge to person with multiple accounts
        second_acct = Account.objects.create()
        second_acct.persons.add(main_person)
        with pytest.raises(MultipleObjectsReturned) as err:
            Person.objects.merge_with(main_person)
        assert "Can't merge with a person record that has multiple accounts" in \
            str(err)
        main_person.delete()

        # copy person details when merging
        main = Person.objects.create(name='Jones')
        prof = Profession.objects.create(name='Professor')
        full = Person.objects.create(name='Jones',
            title='Mr', mep_id="jone.mi", birth_year=1901, death_year=1950,
            viaf_id='http://viaf.org/viaf/123456', sex='M', notes='some details',
            profession=prof)
        acct = Account.objects.create()
        acct.persons.add(main)

        # values should copy over to main fields
        Person.objects.merge_with(main)
        # get fresh copy of main record from db
        main = Person.objects.get(id=main.id)
        assert main.title == full.title
        assert main.mep_id == full.mep_id
        assert main.birth_year == full.birth_year
        assert main.death_year == full.death_year
        assert main.sex == full.sex
        assert main.viaf_id == full.viaf_id
        assert main.profession == full.profession
        assert full.notes in main.notes
        assert 'Merged MEP id %s on %s' % (full.mep_id, iso_date) in main.notes

        # should _not_ copy over existing field values
        full2 = Person.objects.create(name='Jones',
            title='Dr', mep_id="jone.dr", birth_year=1911, notes='more details')
        Person.objects.merge_with(main)
        # get fresh copy of main record from db
        main = Person.objects.get(id=main.id)
        assert main.title != full2.title
        assert main.mep_id != full2.mep_id
        assert main.birth_year != full2.birth_year
        # notes should be appended
        assert full.notes in main.notes
        assert full2.notes in main.notes
        assert 'Merged MEP id %s on %s' % (full2.mep_id, iso_date) in main.notes

        # many-to-many relationships should be shifted to merged person record
        related = Person.objects.create(name='Jonesy')
        jones_jr = Person.objects.create(name='Jonesy Jr.')
        france = Country.objects.create(name='France', code='fr',
            geonames_id='http://www.geonames.org/3017382/')
        germany = Country.objects.create(name='Germany', code='gm',
            geonames_id='http://www.geonames.org/2921044/')
        related.nationalities.add(france, germany)
        info_url = InfoURL.objects.create(person=related, url='http://example.com/')
        info_url2 = InfoURL.objects.create(person=related, url='http://google.com/')
        child = RelationshipType.objects.create(name='child')
        parent = RelationshipType.objects.create(name='parent')
        child_rel = Relationship.objects.create(from_person=related,
            to_person=jones_jr, relationship_type=child)
        parent_rel = Relationship.objects.create(from_person=jones_jr,
            to_person=related, relationship_type=parent)
        # footnote
        src_type = SourceType.objects.create(name='website')
        bibl = Bibliography.objects.create(bibliographic_note='citation',
            source_type=src_type)
        person_contenttype = ContentType.objects.get_for_model(Person)
        fn = Footnote.objects.create(bibliography=bibl, content_type=person_contenttype,
            object_id=related.pk, is_agree=False)

        Person.objects.filter(name='Jonesy').merge_with(main)
        # get fresh copy of main record from db
        main = Person.objects.get(id=main.id)
        assert france in main.nationalities.all()
        assert germany in main.nationalities.all()
        assert info_url in main.urls.all()
        assert info_url2 in main.urls.all()
        assert child_rel in main.from_relationships.all()
        assert parent_rel in main.to_relationships.all()
        assert fn in main.footnotes.all()

        # person with account shared with another person
        sib1 = Person.objects.create(name='sibling')
        sib2 = Person.objects.create(name='sibling2')
        acct = Account.objects.create()
        acct.persons.add(sib1, sib2)

        with pytest.raises(MultipleObjectsReturned) as err:
            Person.objects.merge_with(main)
        assert "Can't merge a person record with a shared account." in \
            str(err)


class TestProfession(TestCase):

    def test_repr(self):
        carpenter = Profession(name='carpenter')
        overall = re.compile(r'<Profession \{.+\}>')
        assert re.search(overall, repr(carpenter))

    def test_str(self):
        carpenter = Profession(name='carpenter')
        assert str(carpenter) == 'carpenter'


class TestRelationship(TestCase):

    def setUp(self):
        self.foo = Person.objects.create(name='Foo')
        self.foo_bro = Person.objects.create(name='Bar')
        self.relationshiptype = RelationshipType.objects.create(name='sibling')
        self.relationship = Relationship.objects.create(
            from_person=self.foo,
            to_person=self.foo_bro,
            relationship_type=self.relationshiptype
        )

    def test_relationship_str(self):
        assert str(self.relationship) == 'Foo is a sibling to Bar.'

    def test_relationship_repr(self):
        assert repr(self.relationship) == (
            "<Relationship {'from_person': <Person Foo>, "
            "'to_person': <Person Bar>, "
            "'relationship_type': <RelationshipType sibling>}>"
        )


class TestRelationshipType(TestCase):
    def test_repr(self):
        sib = RelationshipType(name='sibling')
        overall = re.compile(r'<RelationshipType \{.+\}>')
        assert re.search(overall, repr(sib))

    def test_str(self):
        sib = RelationshipType(name='sibling')
        assert str(sib) == 'sibling'


class TestRelationshipM2M(TestCase):

    def setUp(self):
        self.foo = Person.objects.create(name='Foo')
        self.bar = Person.objects.create(name='Bar')
        self.parent = RelationshipType.objects.create(name='parent')
        Relationship.objects.create(
            from_person=self.foo,
            to_person=self.bar,
            relationship_type=self.parent
        )

        self.baz = Person.objects.create(name='Baz')
        self.partner = RelationshipType.objects.create(name='business partner')

        Relationship.objects.create(
            from_person=self.foo,
            to_person=self.baz,
            relationship_type=self.partner
        )

    def test_relationships(self):
        # Relationship is one sided based on from_person and to_person
        # With the relationship 'parent'

        # foo is parent of bar - should get Foo
        assert (Person.objects.get(from_relationships__relationship_type=self.parent)
                == self.foo)
        # reverse - should get Bar
        assert (Person.objects.get(to_relationships__relationship_type=self.parent)
                == self.bar)
        # foo is partner of bas - should get Baz
        assert (Person.objects.get(to_relationships__relationship_type=self.partner)
                == self.baz)

        # foo is related to both Bar and Baz, so length of 2
        assert len(self.foo.relations.all()) == 2
        # Should still be two if we filter out only Bar and Baz
        # Short way to check if both and only both are in the query set
        assert (len(self.foo.relations.filter(name__in=['Baz', 'Bar']))
                == 2)


class TestAddress(TestCase):

    def test_str(self):
        # Name and city only
        address = Location(name="La Hotel", city="Paris")
        assert str(address) == "La Hotel, Paris"

        # street and city only
        address = Location(street_address="1 Rue Le Foo", city="Paris")
        assert str(address) == "1 Rue Le Foo, Paris"

        # Name, street, and city
        address = Location(street_address="1 Rue Le Foo", city="Paris",
            name="La Hotel")
        assert str(address) == "La Hotel, 1 Rue Le Foo, Paris"

        # city only
        address = Location(city="Paris")
        assert str(address) == "Paris"

    def test_repr(self):
        hotel = Location(name='La Hotel', city='Paris')
        assert repr(hotel).startswith('<Location ')
        assert repr(hotel).endswith('>')
        assert hotel.name in repr(hotel)
        assert hotel.city in repr(hotel)

    def test_latlon_validate(self):
        # Valid, should pass clean fields
        address = Location(latitude=180, longitude=-180, city="Paris")
        address.clean_fields()

        # Not valid, should error out
        with pytest.raises(ValidationError) as err:
            address.latitude = -500
            address.clean_fields()
        assert "Lat/Lon must be between -180 and 180 degrees." in str(err)

        # String should error out too, Django handles the message
        address = Location(latitude="foo", longitude="bar")
        with pytest.raises(ValidationError):
            address.clean_fields()


class TestInfoURL(TestCase):

    def test_str(self):
        p = Person.objects.create(name='Someone')
        info_url = InfoURL(person=p, url='http://example.com/')
        assert str(info_url) == info_url.url

    def test_repr(self):
        p = Person.objects.create(name='Someone')
        info_url = InfoURL(person=p, url='http://example.com/')
        assert repr(info_url).startswith('<InfoURL ')
        assert repr(info_url).endswith('>')
        assert info_url.url in repr(info_url)
        assert str(p) in repr(info_url)


class TestPersonAdmin(TestCase):

    def test_merge_people(self):
        mockrequest = Mock()
        test_ids = ['5', '33', '101']
        # a dictionary mimes the request pattern of access
        mockrequest.session = {}
        mockrequest.POST.getlist.return_value = test_ids
        # code uses the built in methods of a dict, so making GET an
        # actual dict as it is for a request
        mockrequest.GET = {}
        resp = PersonAdmin(Person, Mock()).merge_people(mockrequest, Mock())
        assert isinstance(resp, HttpResponseRedirect)
        assert resp.status_code == 303
        assert resp['location'].startswith(reverse('people:merge'))
        assert resp['location'].endswith('?ids=%s' % ','.join(test_ids))
        # key should be set, but it should be an empty string
        assert 'people_merge_filter' in mockrequest.session
        assert not mockrequest.session['people_merge_filter']
        # Now add some values to be set as a query string on session
        mockrequest.GET = {'p': '3', 'filter': 'foo'}
        resp = PersonAdmin(Person, Mock()).merge_people(mockrequest, Mock())
        assert isinstance(resp, HttpResponseRedirect)
        assert resp.status_code == 303
        assert resp['location'].startswith(reverse('people:merge'))
        assert resp['location'].endswith('?ids=%s' % ','.join(test_ids))
        # key should be set and have a urlencoded string
        assert 'people_merge_filter' in mockrequest.session
        # test agnostic as to order since the querystring
        # works either way
        assert mockrequest.session['people_merge_filter'] in \
            ['p=3&filter=foo', 'filter=foo&p=3']
