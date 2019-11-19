import pytest

from mep.accounts.tests.test_accounts_migrations import TestMigrations


@pytest.mark.last
class TestPersonGenerateSlugs(TestMigrations):

    app = 'people'
    migrate_from = '0015_add_person_optional_slug'
    migrate_to = '0017_person_require_unique_slugs'

    def setUpBeforeMigration(self, apps):
        Person = apps.get_model('people', 'Person')
        self.Person = Person

        # create people to test slug logic
        # - unique last name
        self.hemingway = Person.objects.create(sort_name='Hemingway, Ernest')
        # variants in special characters
        self.erna = Person.objects.create(sort_name='Döblin, Erna Reiss')
        self.alfred = Person.objects.create(sort_name='Döblin, Alfred')
        # variants in case
        self.destaing1 = Person.objects.create(sort_name="D'Estaing")
        self.destaing2 = Person.objects.create(sort_name="d'Estaing")
        # multiples with no last name
        self.adams1 = Person.objects.create(sort_name="Adams")
        self.adams2 = Person.objects.create(sort_name="Adams")
        self.adams3 = Person.objects.create(sort_name="Adams")
        self.adams4 = Person.objects.create(sort_name="Adams")

    def test_slugs(self):
        # slugs should be unique - guaranteed by 0017

        # get fresh copies of records to see changes
        hemingway = self.Person.objects.get(pk=self.hemingway.pk)
        # lastname only if sufficient
        assert hemingway.slug == 'hemingway'
        # group Dö/Dö properly
        erna = self.Person.objects.get(pk=self.erna.pk)
        assert erna.slug == 'doblin-erna-reiss'
        alfred = self.Person.objects.get(pk=self.alfred.pk)
        assert alfred.slug == 'doblin-alfred'
        # group upper/lowercase properly
        destaing1 = self.Person.objects.get(pk=self.destaing1.pk)
        assert destaing1.slug == 'destaing'
        destaing2 = self.Person.objects.get(pk=self.destaing2.pk)
        assert destaing2.slug == 'destaing-2'
        # multiples
        adams1 = self.Person.objects.get(pk=self.adams1.pk)
        adams2 = self.Person.objects.get(pk=self.adams2.pk)
        adams3 = self.Person.objects.get(pk=self.adams3.pk)
        adams4 = self.Person.objects.get(pk=self.adams4.pk)
        assert adams1.slug == 'adams'
        assert adams2.slug == 'adams-2'
        assert adams3.slug == 'adams-3'
        assert adams4.slug == 'adams-4'
