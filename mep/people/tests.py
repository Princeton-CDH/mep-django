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
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Person {'k':v, ...}>""
        overall = re.compile(r'<Person \{.+\}>')
        assert re.search(overall, repr(foo))

    def test_full_name(self):
        foo = Person(last_name='Foo', first_name='Bar')
        assert foo.full_name == 'Bar Foo'

class TestCountry(TestCase):

    def test_repr(self):
        country = Country(name='Foolandia')
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Country {'k':v, ...}>""
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


class TestProfession(TestCase):

    def test_repr(self):
        # No special handling, simple test
        carpenter = Profession(name='carpenter')
        overall = re.compile(r'<Profession \{.+\}>')
        assert re.search(overall, repr(carpenter))

    def test_str(self):
        carpenter = Profession(name='carpenter')
        assert str(carpenter) == 'carpenter'
