# coding=utf-8

import logging

from django.core.exceptions import ObjectDoesNotExist
from eulxml import xmlmap
from viapy.api import ViafEntity

from mep.accounts.models import Account
from mep.people.models import Person

logger = logging.getLogger(__name__)


class TeiXmlObject(xmlmap.XmlObject):
    ROOT_NAMESPACES = {
        't': 'http://www.tei-c.org/ns/1.0'
    }


class Date(TeiXmlObject):
    iso_date = xmlmap.StringField('@when-iso')


class Event(TeiXmlObject):

    e_type = xmlmap.StringField('@type')
    mepid = xmlmap.StringField('t:p/t:persName/@ref')
    name = xmlmap.StringField('t:p/t:persName')


    # duration
    duration_unit = xmlmap.StringField('t:p/t:measure[@type="duration"]/@unit')
    duration_quantity = xmlmap.StringField('t:p/t:measure[@type="duration"]/'
                                           '@quantity')

    # frequency
    frequency_unit = xmlmap.StringField('t:p/t:measure[@type="frequency"]/@unit')
    frequency_quantity = xmlmap.StringField('t:p/t:measure[@type="frequency"]/'
                                            '@quantity')

    # price
    price_unit = xmlmap.StringField('t:p/t:measure[@type="price"]/@unit')
    price_quantity = xmlmap.StringField('t:p/t:measure[@type="price"]/'
                                        '@quantity')

    # deposit
    deposit_unit = xmlmap.StringField('t:p/t:measure[@type="deposit"]/@unit')
    deposit_quantity = xmlmap.StringField('t:p/t:measure[@type="deposit"]/'
                                          '@quantity')

    def to_db_event(self):

        xml_db_mapping = {
            'subscription': 'subscribe',
            'supplement': 'subscribe',
            'borrow': 'borrow',
        }


        mepid = self.mepid.strip('#')
        person = None
        account = None
        try:
            person = Person.objects.get(mepid=mepid)
        except ObjectDoesNotExist:
            person = Person.objects.create(mepid=mepid, name=self.name,
                                           sort_name=self.name)

        try:
            account = Account.objects.get(persons__id=person.id)
        except ObjectDoesNotExist:
            account = Account.objects.create()
            account.save()

        account.person.add(person)
        account.add_event(xml_db_mapping[event])


class DayDiv(TeiXmlObject):
    dates = xmlmap.NodeListField('t:head/t:date', Date)
    events = xmlmap.NodeListField('t:listEvent/t:event', Event)


class LogBook(xmlmap.XmlObject):
    ROOT_NAMESPACES = {
        't': 'http://www.tei-c.org/ns/1.0'
    }

    query = ('//t:body/t:div[@type="year"]/'
             't:div[@type="month"]/t:div[@type="day"]')
    day_divs = xmlmap.NodeListField(query, DayDiv)

    @classmethod
    def from_file(cls, filename):
        return xmlmap.load_xmlobject_from_file(filename, cls)
