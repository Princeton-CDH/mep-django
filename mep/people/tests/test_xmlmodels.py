import os
from unittest.mock import patch

from django.test import TestCase
from eulxml.xmlmap import load_xmlobject_from_string

from mep.people import models
from mep.people.geonames import GeoNamesAPI
from mep.people.xml_models import Person, PersonName, Personography, \
    Nationality, Residence


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fixtures')
XML_FIXTURE = os.path.join(FIXTURE_DIR, 'sample-personography.xml')


class TestPersonography(TestCase):

    def test_from_file(self):
        personog = Personography.from_file(XML_FIXTURE)
        assert isinstance(personog, Personography)
        # fixture currently includes one personog
        assert len(personog.people) == 4
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


class TestNationality(TestCase):

    @patch('mep.people.xml_models.GeoNamesAPI')
    def test_db_country(self, mockgeonames):
        mockgeonames.uri_from_id = GeoNamesAPI.uri_from_id
        # mock geonames country codes (minimal subset)
        mockgeonames.return_value.countries_by_code = {
            'US': {'geonameId': 6252001, 'countryName': 'United States'},
            'MQ': {'geonameId': 3570311, 'countryName': 'Martinique'},
            'FR': {'geonameId': 3017382, 'countryName': 'France'},
        }

        # normal
        nation = load_xmlobject_from_string(
            '''<nationality xmlns="http://www.tei-c.org/ns/1.0" key="fr">France</nationality>''',
            xmlclass=Nationality)
        country = nation.db_country()
        assert country.name == 'France'
        assert country.geonames_id == 'http://sws.geonames.org/3017382/'

        # stateless
        nation = load_xmlobject_from_string(
            '''<nationality xmlns="http://www.tei-c.org/ns/1.0" key="xx">stateless</nationality>''',
            xmlclass=Nationality)
        country = nation.db_country()
        assert country.name == '[no country]'
        assert country.geonames_id == ''

        # no match
        nation = load_xmlobject_from_string(
            '''<nationality xmlns="http://www.tei-c.org/ns/1.0" key="gb">United Kingdom</nationality>''',
            xmlclass=Nationality)
        assert nation.db_country() is None


class TestPersonName(TestCase):
    # xml snippets for testing
    two_firstnames = '''<persName xmlns="http://www.tei-c.org/ns/1.0">
        <surname type="birth">Ellerman</surname>
        <forename sort="1">Anne</forename>
        <forename sort="2">Winifred</forename>
    </persName>'''

    initials = '''<persName xmlns="http://www.tei-c.org/ns/1.0">
        <surname>Collins</surname>
        <forename sort="1" full="init">R</forename>
        <forename sort="2" full="init">F</forename>
    </persName>'''

    married_birth = '''<persName xmlns="http://www.tei-c.org/ns/1.0">
        <surname type="married">Teissier</surname>
        <surname type="birth">Delpech</surname>
        <forename>Jeanine</forename>
    </persName>'''

    multiple = '''<persName xmlns="http://www.tei-c.org/ns/1.0">
        <surname type="married">Hepp</surname>
        <surname type="birth">Saint-René Taillandier</surname>
        <forename sort="1">Henriette</forename>
        <forename sort="2">Sophie</forename>
        <forename sort="3">Marianne</forename>
    </persName>'''

    namelink = '''<persName xmlns="http://www.tei-c.org/ns/1.0">
        <surname sort="1" type="married">Perron</surname>
        <surname sort="2" type="birth">Roos</surname>
        <forename>Elisabeth</forename>
        <nameLink type="married">du</nameLink>
        <nameLink type="birth">de</nameLink>
    </persName>'''

    lastname_only = '''<persName xmlns="http://www.tei-c.org/ns/1.0">
        <surname>Kaopeitzer</surname>
    </persName>'''

    def test_first_name(self):
        # two first name tags with sort attribute
        pname = load_xmlobject_from_string(self.two_firstnames,
            xmlclass=PersonName)
        assert pname.first_name() == 'Anne Winifred'
        # uses sort attributes
        pname.first_names[0].sort = 2
        pname.first_names[1].sort = 1
        assert pname.first_name() == 'Winifred Anne'

        # initials
        pname = load_xmlobject_from_string(self.initials,
            xmlclass=PersonName)
        assert pname.first_name() == 'R. F.'
        # if period is included in xml, shouldn't get duplicated
        pname.first_names[0].value = 'R.'
        assert pname.first_name() == 'R. F.'

    def test_full_name(self):
        # two first name tags with sort attribute
        pname = load_xmlobject_from_string(self.two_firstnames,
            xmlclass=PersonName)
        assert pname.full_name() == 'Anne Winifred Ellerman'

        pname = load_xmlobject_from_string(self.married_birth,
            xmlclass=PersonName)
        assert pname.full_name() == 'Jeanine (Delpech) Teissier'

        pname = load_xmlobject_from_string(self.multiple,
            xmlclass=PersonName)
        assert pname.full_name() == 'Henriette Sophie Marianne (Saint-René Taillandier) Hepp'

        pname = load_xmlobject_from_string(self.namelink,
            xmlclass=PersonName)
        assert pname.full_name() == 'Elisabeth (de Roos) du Perron'

        pname = load_xmlobject_from_string(self.lastname_only,
            xmlclass=PersonName)
        assert pname.full_name() == 'Kaopeitzer'

    def test_sort_name(self):
        # two first name tags with sort attribute
        pname = load_xmlobject_from_string(self.two_firstnames,
            xmlclass=PersonName)
        assert pname.sort_name() == 'Ellerman, Anne Winifred'

        pname = load_xmlobject_from_string(self.married_birth,
            xmlclass=PersonName)
        assert pname.sort_name() == 'Teissier, Jeanine (Delpech)'

        pname = load_xmlobject_from_string(self.multiple,
            xmlclass=PersonName)
        assert pname.sort_name() == 'Hepp, Henriette Sophie Marianne (Saint-René Taillandier)'

        pname = load_xmlobject_from_string(self.namelink,
            xmlclass=PersonName)
        assert pname.sort_name() == 'Perron, Elisabeth (de Roos) du'

        pname = load_xmlobject_from_string(self.lastname_only,
            xmlclass=PersonName)
        assert pname.sort_name() == 'Kaopeitzer'


class TestPerson(TestCase):

    pseudonym = '''<person xml:id="elle.an" xmlns="http://www.tei-c.org/ns/1.0">
        <idno type="viaf">111923629</idno>
        <persName sort="2">
            <surname type="birth">Ellerman</surname>
            <forename sort="1">Anne</forename>
            <forename sort="2">Winifred</forename>
        </persName>
        <persName type="pseudo" sort="1">Bryher</persName>
        <birth>1894</birth>
        <death>1983</death>
        <sex value="F"/>
        <nationality key="gb">United Kingdom of Great Britain and Northern
            Ireland</nationality>
        <note>no address in cards</note>
    </person>'''

    pseudonym_nonprimary = ''' <person xml:id="desc.an" xmlns="http://www.tei-c.org/ns/1.0">
        <idno type="viaf">1900525</idno>
        <persName>
            <surname>Desclos</surname>
            <forename>Anne</forename>
        </persName>
        <persName type="pseudo">Dominique Aury</persName>
        <persName type="pseudo"><forename>Pauline</forename> <surname>Réage</surname></persName>
        <note target="https://en.wikipedia.org/wiki/Anne_Desclos"/>
        <note>daughter of Auguste Desclos</note>
    </person>'''

    def test_properties(self):
        person = Personography.from_file(XML_FIXTURE).people[0]
        assert person.mep_id == "alde.pa"
        assert person.viaf_id == "42635145"
        assert person.title == "Ms"
        assert person.nickname == 'Polly'
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

    @patch('mep.people.xml_models.ViafEntity')
    @patch('mep.people.xml_models.GeoNamesAPI')
    def test_to_db_person(self, mockgeonames, mockviafentity):
        # test with a fairly complete record
        xml_person = Personography.from_file(XML_FIXTURE).people[0]
        mockviaf_record = mockviafentity.return_value
        mockviaf_record.uri = 'http://viaf.org/viaf/%s' % xml_person.viaf_id
        mockviaf_record.birthyear = 1800
        mockviaf_record.deathyear = 1850

        mockgeonames.uri_from_id = GeoNamesAPI.uri_from_id
        # mock geonames country codes (minimal subset)
        mockgeonames.return_value.countries_by_code = {
            'US': {'geonameId': 6252001, 'countryName': 'United States'},
            'MQ': {'geonameId': 3570311, 'countryName': 'Martinique'},
            'FR': {'geonameId': 3017382, 'countryName': 'France'},
        }

        db_person = xml_person.to_db_person()
        assert isinstance(db_person, models.Person)
        assert db_person.mep_id == xml_person.mep_id
        assert db_person.title == xml_person.title
        assert db_person.name == 'Pauline Alderman'
        assert db_person.sort_name == 'Alderman, Pauline'
        assert db_person.birth_year == xml_person.birth
        assert db_person.death_year == xml_person.death
        assert db_person.sex == xml_person.sex

        # first xml note should be ignored because it has no text content
        assert '\n'.join(list(xml_person.notes)[1:]) in db_person.notes
        assert 'Nickname: Polly' in db_person.notes
        # nationality should create country, add relation
        country = db_person.nationalities.first()
        assert country.geonames_id == 'http://sws.geonames.org/6252001/'
        assert country.name == 'United States'
        # urls
        assert db_person.urls.first().url == xml_person.urls[0]
        assert db_person.urls.first().notes == 'URL from XML import'
        # residence addresses
        assert db_person.addresses.first().street_address == \
            xml_person.residences[0].street

        # check viaf handling
        mockviafentity.assert_called_with(xml_person.viaf_id)
        assert db_person.viaf_id == mockviafentity.return_value.uri
        # xml birth/death dates should be used rather than viaf
        assert db_person.birth_year != mockviaf_record.birthyear
        assert db_person.death_year != mockviaf_record.deathyear

        # simulate viaf id with no birth/death date in xml
        del xml_person.birth
        del xml_person.death
        db_person = xml_person.to_db_person()
        # birth/death dates in db should be set from viaf
        assert db_person.birth_year == mockviaf_record.birthyear
        assert db_person.death_year == mockviaf_record.deathyear

        # test with an incomplete record
        xml_person = Personography.from_file(XML_FIXTURE).people[1]
        mockviafentity.reset_mock()
        db_person = xml_person.to_db_person()
        assert db_person.name == 'Kaopeitzer'
        assert db_person.sort_name == 'Kaopeitzer'
        for unknown_field in ['viaf_id', 'sex']:
            assert getattr(db_person, unknown_field) == ''
        for unknown_field in ['birth_year', 'death_year']:
            assert getattr(db_person, unknown_field) is  None

        mockviafentity.assert_not_called()

        # last xml note should be ignored because it has no text content
        assert db_person.notes == '\n'.join(list(xml_person.notes)[:-1])

        # third person in fixture has two nationalities
        xml_person = Personography.from_file(XML_FIXTURE).people[2]
        db_person = xml_person.to_db_person()
        assert db_person.nationalities.count() == 2
        # order is not guaranteed, just check that both expected countries
        # are present
        country_names = [c.name for c in db_person.nationalities.all()]
        assert 'Martinique' in country_names
        assert 'France' in country_names
        country = db_person.nationalities.last()
        geo_ids = [c.geonames_id for c in db_person.nationalities.all()]
        assert 'http://sws.geonames.org/3570311/' in geo_ids
        assert 'http://sws.geonames.org/3017382/' in geo_ids

        # no name
        xml_person = Personography.from_file(XML_FIXTURE).people[3]
        db_person = xml_person.to_db_person()
        assert db_person.name == '[Friend of Renoir]'
        assert db_person.title == ''
        assert db_person.sex == 'M'

        # pseudonym
        xml_person = load_xmlobject_from_string(self.pseudonym, xmlclass=Person)
        db_person = xml_person.to_db_person()
        assert db_person.name == 'Bryher (Anne Winifred Ellerman)'
        assert db_person.sort_name == 'Bryher'

        # pseudonyms, but not primary name
        xml_person = load_xmlobject_from_string(self.pseudonym_nonprimary,
            xmlclass=Person)
        db_person = xml_person.to_db_person()
        assert db_person.name == 'Anne Desclos'
        assert db_person.sort_name == 'Desclos, Anne'
        assert 'Pseudonym(s): Dominique Aury, Pauline Réage' in db_person.notes

