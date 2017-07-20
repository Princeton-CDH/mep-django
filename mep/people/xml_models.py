from eulxml import xmlmap

from mep.people import models


class Person(xmlmap.XmlObject):
    ROOT_NAMESPACES = {
        't': 'http://www.tei-c.org/ns/1.0'
    }

    mep_id = xmlmap.StringField('@xml:id')
    viaf_id = xmlmap.StringField('t:idno[@type="viaf"]')
    last_name = xmlmap.StringField('t:persName/t:surname')
    first_name = xmlmap.StringField('t:persName/t:forename')
    birth = xmlmap.IntegerField('t:birth')
    death = xmlmap.IntegerField('t:death')
    nationality_id = xmlmap.StringField('t:nationality/@key')
    nationality_label = xmlmap.StringField('t:nationality')
    sex = xmlmap.StringField('t:sex/@value')
    notes = xmlmap.StringListField('t:note')
    # todo: handle ref target in notes
    # todo: residence addresses

    def is_imported(self):
        return models.Person.objects.filter(mep_id=self.mep_id).exists()

    def to_db_person(self):
        '''Create a new :class:`mep.people.models.Person` database record
        and populate based on data in the xml.'''
        db_person = models.Person(
            mep_id=self.mep_id,
            first_name=self.first_name or '',
            last_name=self.last_name,
            viaf_id=self.viaf_id or '',  # todo: convert to uri
            birth_year=self.birth or None,
            death_year=self.death or None,
            sex=self.sex or ''
            )
        # todo: notes, addresses, urls

        # db_person.save()  ??
        return db_person


class Personography(xmlmap.XmlObject):
    ROOT_NAMESPACES = {
        't': 'http://www.tei-c.org/ns/1.0'
    }

    people = xmlmap.NodeListField('//t:person', Person)

    @classmethod
    def from_file(cls, filename):
        return xmlmap.load_xmlobject_from_file(filename, cls)
