import os

from django.conf import settings
from django.test import TestCase
from eulxml.xmlmap import load_xmlobject_from_string

from mep.people import models
from mep.people.xml_models import Person, PersonName, Personography, \
    Nationality, Residence


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fixtures')
XML_FIXTURE = os.path.join(FIXTURE_DIR, 'sample-personography.xml')


class TestPersonography(TestCase):

    def test_from_file(self):
        personog = Personography.from_file(XML_FIXTURE)
        assert isinstance(personog, Personography)
        # fixture currently includes one personog
        assert len(personog.people) == 3
        assert isinstance(personog.people[0], Person)
        assert personog.people[0].mep_id == 'alde.pa'


class TestAddress(TestCase):

    def test_properties(self):
        person = Personography.from_file(XML_FIXTURE).people[2]
        # third person in the fixture has a complete address
        assert isinstance(person.residences[0], Residence)
        res = person.residences[0]
        assert res.name == "École normale supérieure"
        assert res.street == "45 Rue d'Ulm"
        assert res.postcode == "75005"
        assert res.city == "Paris"
        assert res.geo == '48.841837, 2.344035'  # sanity check
        assert res.latitude == 48.841837
        assert res.longitude == 2.344035

        # lat/long without geo
        res.geo = ''   # element present but empty
        assert res.latitude is None
        assert res.longitude is None

        del res.geo   # no element present
        assert res.latitude is None
        assert res.longitude is None

    def test_db_address(self):
        # address for third person in the fixture
        res = Personography.from_file(XML_FIXTURE).people[2].residences[0]
        db_address = res.db_address()
        assert isinstance(db_address, models.Address)
        assert db_address.name == res.name
        assert db_address.street_address == res.street
        assert db_address.city == res.city
        assert db_address.postal_code == res.postcode
        assert db_address.latitude == res.latitude
        assert db_address.longitude == res.longitude

        # running again should return the same item
        assert db_address.pk == res.db_address().pk


class TestPersonName(TestCase):

    def test_first_name(self):
        # two first name tags with sort attribute
        pname = load_xmlobject_from_string('''<persName xmlns="http://www.tei-c.org/ns/1.0">
            <surname type="birth">Ellerman</surname>
            <forename sort="1">Anne</forename>
            <forename sort="2">Winifred</forename>
        </persName>''', xmlclass=PersonName)
        assert pname.first_name() == 'Anne Winifred'

        # initials
        pname = load_xmlobject_from_string('''<persName xmlns="http://www.tei-c.org/ns/1.0">
            <surname>Collins</surname>
            <forename sort="1" full="init">R</forename>
            <forename sort="2" full="init">F</forename>
        </persName>''', xmlclass=PersonName)
        assert pname.first_name() == 'R. F.'

        # if period is included in xml, shouldn't get duplicated
        pname.first_names[0].value = 'R.'
        assert pname.first_name() == 'R. F.'


class TestPerson(TestCase):

    def test_properties(self):
        person = Personography.from_file(XML_FIXTURE).people[0]
        assert person.mep_id == "alde.pa"
        assert person.viaf_id == "42635145"
        assert person.last_name == "Alderman"
        assert person.first_name == "Pauline"
        assert person.title == "Ms"
        assert person.birth == 1893
        assert person.death == 1983
        assert person.sex == "F"
        assert isinstance(person.nationalities[0], Nationality)
        assert person.nationalities[0].code == "us"
        assert person.nationalities[0].label == "United States of America"
        assert len(person.notes) == 3
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
        assert db_person.title == xml_person.title
        assert db_person.viaf_id == 'http://viaf.org/viaf/%s' % xml_person.viaf_id
        # TODO revision to full/sort name
        # assert db_person.first_name == xml_person.first_name
        # assert db_person.last_name == xml_person.last_name
        assert db_person.birth_year == xml_person.birth
        assert db_person.death_year == xml_person.death
        assert db_person.sex == xml_person.sex
        # first xml note should be ignored because it has no text content
        assert db_person.notes == '\n'.join(list(xml_person.notes)[1:])
        # nationality should create country, add relation
        country = db_person.nationalities.first()
        assert country.code == 'us'
        assert country.name == 'United States of America'
        # urls
        assert db_person.urls.first().url == xml_person.urls[0]
        assert db_person.urls.first().notes == 'URL from XML import'
        # residence addresses
        assert db_person.addresses.first().street_address == \
            xml_person.residences[0].street

        # test with a incomplete record
        xml_person = Personography.from_file(XML_FIXTURE).people[1]
        db_person = xml_person.to_db_person()
        # TODO revise full/sort name
        # assert db_person.last_name == 'Kaopeitzer'
        # for unknown_field in ['first_name', 'viaf_id', 'sex']:
        for unknown_field in ['viaf_id', 'sex']:
            assert getattr(db_person, unknown_field) == ''
        for unknown_field in ['birth_year', 'death_year']:
            assert getattr(db_person, unknown_field) is  None

        # last xml note should be ignored because it has no text content
        assert db_person.notes == '\n'.join(list(xml_person.notes)[:-1])

        # third person in fixture has two nationalities
        xml_person = Personography.from_file(XML_FIXTURE).people[2]
        db_person = xml_person.to_db_person()
        assert db_person.nationalities.count() == 2
        country = db_person.nationalities.first()
        assert country.code == 'mq'
        assert country.name == 'Martinique'
        country = db_person.nationalities.last()
        assert country.code == 'fr'
        assert country.name == 'France'


