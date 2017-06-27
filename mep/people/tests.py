import re

from django.test import TestCase

from .models import Country, Person, Profession, Relationship, RelationshipType


class TestPerson(TestCase):

    def test_str(self):
        # Last name should appear as lastname,
        foo = Person(last_name='Foo')
        assert str(foo) == 'Foo,'

        # Full name should be Foo, Bar
        foo_bar = Person(last_name='Foo', first_name='Bar')
        assert str(foo_bar) == 'Foo, Bar'

    def test_repr(self):
        # Foo Bar, born 1900
        foo = Person(last_name='Foo', first_name='Bar', birth_year=1900)
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Person {'k':v, ...}>""
        overall = re.compile(r'<Person \{.+\}>')
        assert re.search(overall, repr(foo))

    def test_full_name(self):
        foo = Person(last_name='Foo', first_name='Bar')
        assert foo.full_name == 'Bar Foo'


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
        self.foo = Person.objects.create(last_name='Foo')
        self.foo_bro = Person.objects.create(last_name='Bar')
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
        self.foo = Person.objects.create(last_name='Foo')
        self.bar = Person.objects.create(last_name='Bar')
        self.parent = RelationshipType.objects.create(name='parent')
        Relationship.objects.create(
            from_person=self.foo,
            to_person=self.bar,
            relationship_type=self.parent
        )

        self.baz = Person.objects.create(last_name='Baz')
        self.partner = RelationshipType.objects.create(name='business partner')

        Relationship.objects.create(
            from_person=self.foo,
            to_person=self.baz,
            relationship_type=self.partner
        )

    def test_m2m_relationships(self):
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
        assert (len(self.foo.relations.filter(last_name__in=['Baz', 'Bar']))
                == 2)
