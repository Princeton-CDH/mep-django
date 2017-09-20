# coding=utf-8

import logging

from eulxml import xmlmap
from viapy.api import ViafEntity

from mep.people import models
from mep.people.geonames import GeoNamesAPI


logger = logging.getLogger(__name__)


class TeiXmlObject(xmlmap.XmlObject):
    ROOT_NAMESPACES = {
        't': 'http://www.tei-c.org/ns/1.0'
    }

class Nationality(TeiXmlObject):
    '''Nationality associated with a :class:`Person`'''
    code = xmlmap.StringField('@key')
    label = xmlmap.StringField('normalize-space(.)')
    not_after = xmlmap.StringField('@notAfter')
    not_before = xmlmap.StringField('@notBefore')

    def db_country(self):
        geonamesapi = GeoNamesAPI()

        # special case: "stateless" (only occurs once)
        if self.label == 'stateless':
            # no geonames id or code
            name = '[no country]'
            geo_id = ''
            code = ''

        elif self.code.upper() in geonamesapi.countries_by_code:
            geoname = geonamesapi.countries_by_code[self.code.upper()]
            name = geoname['countryName']
            geo_id = GeoNamesAPI.uri_from_id(geoname['geonameId'])
            code = geoname['countryCode']

        else:
            logger.warn('country code %s not found', self.code.upper())
            return

        # get existing country or add if not yet present
        country, created = models.Country.objects.get_or_create(
            geonames_id=geo_id,
            name=name,
            code=code
        )
        return country


class Residence(TeiXmlObject):
    '''Residence associated with a :class:`Person`'''
    name = xmlmap.StringField('t:address/t:name|t:address/t:name', normalize=True)
    street = xmlmap.StringField('t:address/t:street', normalize=True)
    postcode = xmlmap.StringField('t:address/t:postCode', normalize=True)
    city = xmlmap.StringField('t:address/t:settlement', normalize=True)
    # lat/long are in a single <geo> field, separated by a comma
    geo = xmlmap.StringField('t:geo')
    latitude = xmlmap.FloatField('substring-before(t:geo, ",")')
    longitude = xmlmap.FloatField('substring-after(t:geo, ",")')

    #: list of cities in the xml with known, unambiguous countries
    #: provided by MEP team for import
    city_country = {
        "Paris": 'FR',
        "Neuilly-sur-Seine": 'FR',
        "Nice": 'FR',
        "Rome": 'IT',
        "Le Lavandaou": 'FR',
        "La Teste-de-Buch": 'FR',
        "La Croix": 'FR',
        "Vanves": 'FR',
        "Versailles": 'FR',
        "Asnières-sur-Seine": 'FR',
        "Vitry-sur-Seine": 'FR',
        "Bitche": 'FR',
        "Orléans": 'FR',
        "Fontenay-aux-Roses": 'FR',
        "Ville-d'Avray": 'FR',
        "Sceaux": 'FR',
        "London": 'GB',
        "Villecresnes": 'FR',
        "Dalton": 'GB',
        "Cambridge": 'GB',
        "Toulouse": 'FR',
        "Sartilly": 'FR',
        "Saint-Germain-en-Laye": 'FR',
        "Saint Enogat": 'FR',
        "Blennes": 'FR',
        "Asnières-sous-Bois": 'FR',
        "Montsoult": 'FR',
        "Copenhagen": 'DK',
        "Bougival": 'FR',
        "Châtenay-Malabry": 'FR',
        "Saint-Magne-de-Castillon": 'FR',
        "Arras": 'FR',
        "New York": 'US',
        "Rueil-Malmaison": 'FR',
        "Berck": 'FR',
        "Marnes la Coquette": 'FR',
        "Le Mesnil-sur-Blangy": 'FR',
        "Laguépie": 'FR',
        "Cazoulès": 'FR',
        "Zürich": 'CH',
        "Courbevoie": 'FR',
        "Pornic": 'FR',
        "Witten": 'DE',
        "Lot-et-Garonne": 'FR',
        "Gstaad": 'CH',
        "Madrid": 'ES',
        "Antibes": 'FR',
        "Key West": 'US',
        "Barcelona": 'ES',
        "Beauvais": 'FR',
        "Boulogne-Billancourt": 'FR',
        "Chicago": 'US',
        "Trieste": 'IT',
        "Rouen": 'FR',
        "Saint-Mandé": 'FR',
        "Nogent-sur-Marne": 'FR',
        "Champagné-Saint-Hilaire": 'FR',
        "Trouville-sur-Mer": 'FR',
        "Shoreham-by-Sea": 'GB',
        "Le Bourg Dun": 'FR',
        "Saint-Pierre-d'Albigny": 'FR',
        "Menton": 'FR',
        "Strasbourg": 'FR',
        "Vichy": 'FR',
        "Lodève": 'FR',
        "Neuilly": 'FR',
        "Saint-Cloud": 'FR',
        "Varengeville-sur-Mer": 'FR',
        "Sassetot-le-Mauconduit": 'FR',
        "Le Vésinet": 'FR',
        "Ixelles": 'BE',
        "Ermont": 'FR',
        "Allouis": 'FR',
        "Arcachon": 'FR',
        "Agon Coutainville": 'FR',
        "Brooklyn": 'US',
        "Le Beausset": 'FR',
        "Fontainebleau": 'FR',
        "Vernouillet": 'FR',
        "Ville d'Avray": 'FR',
        "Grasse": 'FR',
        "Hautot-sur-Mer": 'FR',
        "Vesoul": 'FR',
        "Hyères": 'FR',
        "Edinburgh": 'GB',
        "Lille": 'FR',
        "Le Chesnay": 'FR',
        "Biarritz": 'FR',
        "Sèvres": 'FR',
        "Villers-sur-Mer": 'FR',
        "Brest": 'FR',
        "Cachan": 'FR',
        "West Hollywood": 'US',
        "München": 'DE',
        "Courteilles": 'FR',
        "Brunnen": 'CH',
        "Arcueil": 'FR',
        "Clamart": 'FR',
        "Nogent-le-Rotrou": 'FR',
        "Omonville-la-Rogue": 'FR',
        "Champeaux": 'FR',
        "Toulon": 'FR',
        "Douai": 'FR',
        "La Bourboule": 'FR',
        "Warehorne": 'GB',
        "Cagnes-sur-Mer": 'FR',
        "Gargenville": 'FR',
        "Montgaillard": 'FR',
        "New York": 'US',
        "La Madelaine": 'FR',
        "Nevers": 'FR',
        "Nantes": 'FR',
        "Bègles": 'FR',
        "Levallois-Perret": 'FR',
        "Parkersburg": 'US',
        "Angers": 'FR',
        "Nimes": 'FR',
        "Lezigne": 'FR',
        "L'Haÿ-les-Roses": 'FR',
        "Les Praz de Chamonix": 'FR',
        "Courmayeur": 'IT',
        "Le Pouldu": 'FR',
        "Issy-les-Moulineaux": 'FR',
        "Saint-Servan": 'FR',
        "Vignoux-sur-Barangeon": 'FR',
        "Mortagne-sur-Sèvre": 'FR',
        "Vernet-les-Bains": 'FR',
        "Shanghai": 'CN',
        "Bagnoles-de-l'Orne": 'FR',
        "Côtes-d'Armor": 'FR',
    }

    def db_address(self):
        '''Get the corresponding :class:`mep.people.models.Address` in the
        database, creating a new address if it does not exist.'''
        addr, created = models.Address.objects.get_or_create(
            name=self.name or '',
            street_address=self.street or '',
            city=self.city or '',
            postal_code=self.postcode or '',
            # NOTE: including lat/long in the get or create call
            # results in a new address getting created with the same values.
            defaults={
                'latitude': self.latitude,
                'longitude': self.longitude,
            }
        )
        # city has a known country, add that
        if self.city in self.city_country:
            # TODO: move country from geonames code logic into db model
            geonamesapi = GeoNamesAPI()
            geoname = geonamesapi.countries_by_code[self.city_country[self.city]]
            # get existing country or add if not yet present
            country, created = models.Country.objects.get_or_create(
                geonames_id=GeoNamesAPI.uri_from_id(geoname['geonameId']),
                name=geoname['countryName'],
                code=geoname['countryCode']
            )
            addr.country = country

        # NOTE: if we have both lat/long and country, could check
        # and warn if lat/long do not match
        # (or if we have only lat/long, could lookup country)

        return addr

class Name(TeiXmlObject):
    name_type = xmlmap.StringField('@type')
    sort = xmlmap.IntegerField('@sort')
    full = xmlmap.StringField('@full')
    value = xmlmap.StringField('text()')

    def __str__(self):
        if self.full == 'init':
            return '%s.' % self.value.strip('.')
        return self.value


class PersonName(TeiXmlObject):
    last_names = xmlmap.NodeListField('t:surname', Name)
    first_names = xmlmap.NodeListField('t:forename', Name)
    married_name = xmlmap.NodeField('t:surname[@type="married"]', Name)
    birth_name = xmlmap.NodeField('t:surname[@type="birth"]', Name)
    sort = xmlmap.IntegerField('@sort')

    namelink = xmlmap.StringField('t:nameLink')
    birth_namelink = xmlmap.StringField('t:nameLink[@type="birth"]')
    married_namelink = xmlmap.StringField('t:nameLink[@type="married"]')

    def full_name(self):
        '''Combine first and last names into "firstname lastname" or
        "firstname (birth name) married name".  Handles multiple first names,
        initials, etc.'''
        return ' '.join(
            # exclude any empty values
            [name for name in
                [self.first_name(), self.display_birthname(), self.last_name()]
            if name])

    def sort_name(self):
        '''Combine first and last names into "lastname, firstname" or
        "married name, firstname (birth name)".  Handles multiple first names,
        initials, etc.'''
        first_name = ' '.join(
            [name for name in [self.first_name(), self.display_birthname(),
                               self.married_namelink or self.namelink]
             if name])
        return ', '.join([n for n in [self.last_name(sort=True), first_name] if n])

    def display_birthname(self):
        # in some cases only one name is present but it is tagged as birth name
        if self.birth_name and self.married_name:
            birth_name = ' '.join([self.birth_namelink or '',
                                   str(self.birth_name)])
            return '(%s)' % birth_name.strip()
        return ''

    def last_name(self, sort=False):
        # if married name is set, return that
        if self.married_name:
            lastname = str(self.married_name)
        # special case: one person with no name
        elif not self.last_names:
            return ''
        # otherwise, just use the first last name
        else:
            lastname = str(self.last_names[0])

        # in non-sorting mode, if a namelink is present (de, du, de la, etc)
        # include it
        if not sort and (self.married_namelink or self.namelink):
            return ' '.join([self.married_namelink or self.namelink, lastname])

        return lastname

    def first_name(self):
        # handle multiple first names
        sorted_names = sorted(self.first_names, key=lambda n: n.sort or 0)
        return ' '.join([str(n) for n in sorted_names])

class Note(TeiXmlObject):

    def __str__(self):
        # check for included person name with ref id
        for node in self.node:
            if node.tag == '{http://www.tei-c.org/ns/1.0}persName':
                # if ref is set, add it to the text after the person name
                ref = node.get('ref')
                if ref and ref not in node.tail:  # only add once
                    node.tail = ' [%s] %s' % (ref, node.tail)

        # output note text normally, now including ref id
        return self.node.xpath("normalize-space(.)")

class Person(TeiXmlObject):
    mep_id = xmlmap.StringField('@xml:id')
    viaf_id = xmlmap.StringField('t:idno[@type="viaf"]')
    title = xmlmap.StringField('t:persName/t:roleName')
    names = xmlmap.NodeListField('t:persName', PersonName)
    pseudonyms = xmlmap.NodeListField('t:persName[@type="pseudo"]', PersonName)
    nickname = xmlmap.StringField('./t:persName/t:addName[@type="nickname"]')
    birth = xmlmap.IntegerField('t:birth')
    death = xmlmap.IntegerField('t:death')
    sex = xmlmap.StringField('t:sex/@value')
    notes = xmlmap.NodeListField('t:note', Note)
    urls = xmlmap.StringListField('.//t:ref/@target')
    nationalities = xmlmap.NodeListField('t:nationality', Nationality)
    # todo: handle ref target in notes
    residences = xmlmap.NodeListField('t:residence', Residence)

    def is_imported(self):
        return models.Person.objects.filter(mep_id=self.mep_id).exists()

    def to_db_person(self):
        '''Create a new :class:`mep.people.models.Person` database record
        and populate based on data in the xml.'''

        db_person = models.Person(
            mep_id=self.mep_id,
            title=self.title or '',
            birth_year=self.birth or None,
            death_year=self.death or None,
            sex=self.sex or ''
        )
        # Combine any non-empty notes from the xml and put them in the
        # database notes field. (URLs are handled elsewhere)
        db_person.notes = '\n'.join(str(note) for note in self.notes
                                    if str(note).strip())

        # handle names
        # - simple case: only one name in the xml
        if len(self.names) == 1:
            # special case: one entry with no name ("friend of renoir")
            if not self.names[0].last_name():
                db_person.name = '[%s]' % self.title.strip()
                db_person.title = ''

            else:
                db_person.name = self.names[0].full_name()
                db_person.sort_name = self.names[0].sort_name()

        # handle multiple names
        else:
            # check for pseudonym
            if self.pseudonyms:
                # pseudonym is primary name
                if self.pseudonyms[0].sort == 1:
                    pseudonym = [str(self.pseudonyms[0])]
                    sur = self.pseudonyms[0].last_name()
                    fore = self.pseudonyms[0].first_name()
                    if sur and fore:
                        pseudonym = [str(fore), str(sur)]
                    db_person.name = '%s (%s)' % \
                        (" ".join(pseudonym), self.names[0].full_name())
                    db_person.sort_name = self.pseudonyms[0].sort_name() \
                        or str(self.pseudonyms[0])

                # pseudonym is not primary
                else:
                    # use the first name
                    db_person.name = self.names[0].full_name()
                    db_person.sort_name = self.names[0].sort_name()

                    # document any pseudonyms in the notes
                    db_person.notes += '\nPseudonym(s): %s' % \
                        ', '.join([str(n) for n in self.pseudonyms])

        # add nickname to notes, if any
        if self.nickname:
            db_person.notes += '\nNickname: %s' % self.nickname

        # Set VIAF information if available
        if self.viaf_id:
            viaf_record = ViafEntity(self.viaf_id)
            db_person.viaf_id = viaf_record.uri
            # birth/death dates from xml take precedence; but if they are
            # not set, set them from viaf
            if db_person.birth_year is None:
                db_person.birth_year = viaf_record.birthyear
            if db_person.death_year is None:
                db_person.death_year = viaf_record.deathyear

            # TODO: possible to get authorized name from VIAF?
            # NOTE: could also get wikidata or other sameAs urls for some

        # record must be saved before adding relations to other tables
        db_person.save()

        # handle nationalities; could be multiple
        for nation in self.nationalities:
            country = nation.db_country()
            if country:
                db_person.nationalities.add(country)

        # special case: add note for not after/before
        if self.nationalities and \
          (self.nationalities[0].not_after or self.nationalities[0].not_before):
            note_text = ['Nationality:  ']
            for nation in self.nationalities:
                if nation.not_after:
                    note_text.append('%s notAfter %s' % \
                        (nation.label, nation.not_after))
                if nation.not_before:
                    note_text.append('%s notBefore %s' % \
                        (nation.label, nation.not_before))

            db_person.notes += ' '.join(note_text)
            db_person.save()

        # handle URLs included in notes
        for link in self.urls:
            db_person.urls.add(models.InfoURL.objects.create(url=link,
                person=db_person, notes='URL from XML import'))

        # handle residence addresses
        for res in self.residences:
            db_person.addresses.add(res.db_address())

        return db_person


class Personography(xmlmap.XmlObject):
    ROOT_NAMESPACES = {
        't': 'http://www.tei-c.org/ns/1.0'
    }

    people = xmlmap.NodeListField('//t:person', Person)

    @classmethod
    def from_file(cls, filename):
        return xmlmap.load_xmlobject_from_file(filename, cls)
