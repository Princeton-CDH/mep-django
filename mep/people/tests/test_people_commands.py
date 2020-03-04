from io import StringIO

from django.test import TestCase

from mep.people.models import Person
from mep.people.management.commands import export_members


class TestExportMembers(TestCase):
    fixtures = ['sample_people']

    def setUp(self):
        self.cmd = export_members.Command()
        self.cmd.stdout = StringIO()

    def test_get_queryset(self):
        # queryset should only include library members
        member = Person.objects.get(pk=189)  # francisque gay, member
        author = Person.objects.get(pk=7152) # aeschylus, non-member
        qs = self.cmd.get_queryset()
        self.assertTrue(member in qs)
        self.assertFalse(author in qs)

    def test_get_object_data(self):
        # fetch some example people from fixture & call get_object_data
        gay = Person.objects.get(name='Francisque Gay')
        hemingway = Person.objects.get(name='Ernest Hemingway')
        gay_data = self.cmd.get_object_data(gay)
        hemingway_data = self.cmd.get_object_data(hemingway)

        # check some basic data
        self.assertEqual(gay_data['name'], 'Francisque Gay')
        self.assertEqual(gay_data['gender'], 'M')
        self.assertEqual(gay_data['birth year'], 1885)
        self.assertEqual(hemingway_data['sort name'], 'Hemingway, Ernest')
        self.assertEqual(hemingway_data['death year'], 1961)
        self.assertFalse('title' in hemingway_data) # empty fields not present

        # check nationalities
        self.assertTrue('France' in gay_data['nationalities'])
        self.assertTrue('United States' in hemingway_data['nationalities'])

        # check viaf & wikipedia urls
        self.assertEqual(hemingway_data['wikipedia url'],
                         'https://en.wikipedia.org/wiki/Ernest_Hemingway')
        self.assertEqual(gay_data['viaf url'], 'http://viaf.org/viaf/9857613')

        # check addresses & coordinates
        self.assertTrue('3 Rue Garancière, Paris' in gay_data['addresses'])
        self.assertTrue('48.85101, 2.33590' in gay_data ['coordinates'])

