import re

from django.test import TestCase

from .models import Country, Person, Profession


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
        # Using self.__dict__ for maximum detail, so we can't count on order
        # Testing for things that should be there and overall setup.
        # should be of the form "<Person: {'k':v, ...}>""
        overall = re.compile(r'<Person \{.+\}>')
        assert re.search(overall, repr(foo))

        # Sample some fields, but don't want to break this too readily with
        # detail changes either
        assert "'first_name': 'Bar'" in repr(foo)
        assert "'last_name': 'Foo'" in repr(foo)
        assert "'start_year': 1900" in repr(foo)
        # Some fields that should get None or ''
        assert "'end_year': None" in repr(foo)
        assert "'sex': ''" in repr(foo)

    def test_nationalities(self):
        '''Confirm that m2m functionality is as expected for nationalities'''

        # No need to test Django methods, just verifying the link is
        # semantically sane.
        # These tests may be superfluous but making sure of expected behavior
        # in dev.
        foolandia = Country.objects.create(name='Foolandia')
        zanzibar = Country.objects.create(name='Zanzibar')
        person = Person.objects.create(last_name='Baz')

        # Set all of them at once
        person.nationalities.set([foolandia, zanzibar])
        queryset = person.nationalities.all()
        # They exist on person object
        assert foolandia in queryset
        assert zanzibar in queryset


class TestCountry(TestCase):

    def test_repr(self):
        country = Country(name='Foolandia')
        # Using self.__dict__ for maximum detail, so we can't count on order
        # Testing for things that should be there and overall setup.
        # should be of the form "<Country: {'k':v, ...}>""
        overall = re.compile(r'<Country \{.+\}>')
        assert re.search(overall, repr(country))

        # Sample specific field behavior
        assert "'name': 'Foolandia'" in repr(country)
        assert "'code': ''" in repr(country)
        # Add a code
        country.code = 'foo'
        assert "'code': 'foo'" in repr(country)

    def test_str(self):
        assert str(Country(name='Foolandia')) == 'Foolandia'

    def test_nationalities(self):
        # same block as mirror in test_nationalities
        foolandia = Country.objects.create(name='Foolandia')
        zanzibar = Country.objects.create(name='Zanzibar')
        person = Person.objects.create(last_name='Baz')
        person.nationalities.set([foolandia, zanzibar])

        # Check the reverse relationship
        assert foolandia.person_set.first() == person
        assert zanzibar.person_set.first() == person


class TestProfession(TestCase):

    def test_repr(self):
        # No special handling, simple test
        carpenter = Profession(name='carpenter')
        overall = re.compile(r'<Profession \{.+\}>')
        assert re.search(overall, repr(carpenter))

    def test_str(self):
        carpenter = Profession(name='carpenter')
        assert str(carpenter) == 'carpenter'
