import re

from django.core.exceptions import ValidationError
from django.test import TestCase
import pytest

from mep.people.models import InfoURL, Person, Profession, Relationship, \
    RelationshipType, Address


class TestPerson(TestCase):

    def test_str(self):
        # Use name if sort name is not set
        person_foo = Person(name='Foo')
        assert str(person_foo) == 'Foo'

        # Use sort name if available
        foo_bar = Person(name='Foo Bar', sort_name='Bar, Foo')
        assert str(foo_bar) == 'Bar, Foo'

    def test_repr(self):
        # Foo Bar, born 1900
        person_foo = Person(name='Foo', sort_name='Bar, Foo', birth_year=1900)
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Person {'k':v, ...}>""
        overall = re.compile(r'<Person \{.+\}>')
        assert re.search(overall, repr(person_foo))


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

        # Should get Foo
        assert (Person.objects.get(from_person__relationship_type=self.parent)
                == self.foo)
        # Should get Bar
        assert (Person.objects.get(to_person__relationship_type=self.parent)
                == self.bar)
        # Should get Baz
        assert (Person.objects.get(to_person__relationship_type=self.partner)
                == self.baz)

        # Should be Bar and Baz, so length of 2
        assert len(self.foo.relations.all()) == 2
        # Should still be two if we filter out only Bar and Baz
        # Short way to check if both and only both are in the query set
        assert (len(self.foo.relations.filter(name__in=['Baz', 'Bar']))
                == 2)


class TestAddress(TestCase):

    def test_str(self):
        # Name and city only
        address = Address(name="La Hotel", city="Paris")
        assert str(address) == "La Hotel, Paris"

        # street and city only
        address = Address(street_address="1 Rue Le Foo", city="Paris")
        assert str(address) == "1 Rue Le Foo, Paris"

        # Name, street, and city
        address = Address(street_address="1 Rue Le Foo", city="Paris",
            name="La Hotel")
        assert str(address) == "La Hotel, 1 Rue Le Foo, Paris"

        # city only
        address = Address(city="Paris")
        assert str(address) == "Paris"

    def test_latlon_validate(self):
        # Valid, should pass clean fields
        address = Address(latitude=180, longitude=-180, city="Paris")
        address.clean_fields()

        # Not valid, should error out
        with pytest.raises(ValidationError) as err:
            address.latitude = -500
            address.clean_fields()
        assert "Lat/Lon must be between -180 and 180 degrees." in str(err)

        # String should error out too, Django handles the message
        address = Address(latitude="foo", longitude="bar")
        with pytest.raises(ValidationError):
            address.clean_fields()


