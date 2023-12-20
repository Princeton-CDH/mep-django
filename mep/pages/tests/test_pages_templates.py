from datetime import datetime

from django.template.loader import get_template
from django.test import TestCase
from django.utils.html import strip_tags

from mep.pages.models import Person


class TestCitation(TestCase):
    def setUp(self):
        # mock context
        self.context = {
            "page": {
                "authors": [],
                "title": "About the Library",
                "first_published_at": datetime(2020, 1, 1),
                "get_full_url": "http://example.com/",
            },
            "SW_VERSION": "test",
        }
        self.template = get_template("pages/snippets/citation.html")

    def test_no_author(self):
        result = self.template.render(self.context)
        assert '<span class="authors">' not in result

    def test_single_author(self):
        # add a single author - displays as "lastname, first."
        p1 = Person.objects.create(first_name="Karl", last_name="Marx")
        self.context["page"]["authors"].append({"value": p1})

        result = strip_tags(self.template.render(self.context))
        assert "Marx, Karl." in result

    def test_two_authors(self):
        # add two authors: "lastname, first and firstname lastname.""
        p1 = Person.objects.create(first_name="Karl", last_name="Marx")
        p2 = Person.objects.create(first_name="Friedrich", last_name="Engels")

        self.context["page"]["authors"].append({"value": p1})
        self.context["page"]["authors"].append({"value": p2})

        result = strip_tags(self.template.render(self.context))
        assert "Marx, Karl and Friedrich Engels." in result

    def test_three_authors(self):
        # for 3+ authors: "lastname, firstname, first last, and first last."
        p1 = Person.objects.create(first_name="Karl", last_name="Marx")
        p2 = Person.objects.create(first_name="Friedrich", last_name="Engels")
        p3 = Person.objects.create(first_name="John", last_name="Smith")

        self.context["page"]["authors"].append({"value": p1})
        self.context["page"]["authors"].append({"value": p2})
        self.context["page"]["authors"].append({"value": p3})

        result = strip_tags(self.template.render(self.context))
        assert "Marx, Karl, Friedrich Engels, and John Smith." in result
