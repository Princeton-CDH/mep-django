import re

from django.test import TestCase

from .models import Person


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
        # should be of the form '<Person: {kv}>'
        overall = re.compile(r'<Person: \{.+\}>')
        assert re.search(overall, repr(foo))

        # Sample some fields, but don't want to break this too readily with
        # detail changes either
        assert "'first_name': 'Bar'" in repr(foo)
        assert "'last_name': 'Foo'" in repr(foo)
        assert "'start_year': 1900" in repr(foo)
        # Some fields that should get None or ''
        assert "'end_year': None" in repr(foo)
        assert "'sex': ''" in repr(foo)

    def test_validate_years(self):
        foo = Person(last_name='Foo', birth_year=1900)
