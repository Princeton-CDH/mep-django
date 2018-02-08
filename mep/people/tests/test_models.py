import re
from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase
import pytest
from viapy.api import ViafEntity

from mep.people.models import InfoURL, Person, Profession, Relationship, \
    RelationshipType, Location, Country
from mep.accounts.models import Account, Subscription, Reimbursement


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

        # add an address
        address = Location.objects.create(name='L\'Hotel', city='Paris')
        pers.addresses.add(address)
        # should be one
        assert pers.address_count() == 1

        # add another, should be 2
        address2 = Location.objects.create(name='Elysian Fields', city='Paris')
        pers.addresses.add(address2)
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
        assert repr(hotel).startswith('<Address ')
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
