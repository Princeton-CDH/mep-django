import os

from django.conf import settings
from django.test import TestCase

from mep.people import models
from mep.people.xml_models import Person, Personography

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fixtures')
XML_FIXTURE = os.path.join(FIXTURE_DIR, 'sample-personography.xml')


class TestPersonography(TestCase):

    def test_from_file(self):
        personog = Personography.from_file(XML_FIXTURE)
        assert isinstance(personog, Personography)
        # fixture currently includes one personog
        assert len(personog.people) == 2
        assert isinstance(personog.people[0], Person)
        assert personog.people[0].mep_id == 'alde.pa'


class TestPerson(TestCase):

    def test_properties(self):
        person = Personography.from_file(XML_FIXTURE).people[0]
        assert person.mep_id == "alde.pa"
        assert person.viaf_id == "42635145"
        assert person.last_name == "Alderman"
        assert person.first_name == "Pauline"
        assert person.birth == 1893
        assert person.death == 1983
        assert person.sex == "F"
        assert person.nationality_id == "us"
        assert person.nationality_label == "United States of America"
        assert len(person.notes) == 2
        assert person.notes[1] == 'test second note'

    def test_is_imported(self):
        # fixture is not yet in the database
        xml_person = Personography.from_file(XML_FIXTURE).people[0]
        assert not xml_person.is_imported()

        # save in the database and check again
        xml_person.to_db_person().save()
        assert xml_person.is_imported()

    def test_to_db_person(self):
        # test with a fairly complete record
        xml_person = Personography.from_file(XML_FIXTURE).people[0]
        db_person = xml_person.to_db_person()
        assert isinstance(db_person, models.Person)
        assert db_person.mep_id == xml_person.mep_id
        assert db_person.viaf_id == xml_person.viaf_id  # todo: needs viaf uri
        assert db_person.first_name == xml_person.first_name
        assert db_person.last_name == xml_person.last_name
        assert db_person.birth_year == xml_person.birth
        assert db_person.death_year == xml_person.death
        assert db_person.sex == xml_person.sex

        # todo: nationality, notes, addresses

        # test with a incomplete record
        xml_person = Personography.from_file(XML_FIXTURE).people[1]
        db_person = xml_person.to_db_person()
        assert db_person.last_name == 'Kaopeitzer'
        for unknown_field in ['first_name', 'viaf_id', 'sex']:
            assert getattr(db_person, unknown_field) == ''
        for unknown_field in ['birth_year', 'death_year']:
            assert getattr(db_person, unknown_field) == None


