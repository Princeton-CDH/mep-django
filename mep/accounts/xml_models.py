# coding=utf-8
import logging
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from eulxml import xmlmap
from viapy.api import ViafEntity
from datetime import datetime, timedelta

import sys
from mep.accounts.models import Account, Subscribe
from mep.people.models import Person


class TeiXmlObject(xmlmap.XmlObject):
    ROOT_NAMESPACES = {
        't': 'http://www.tei-c.org/ns/1.0'
    }



class XmlEvent(TeiXmlObject):

    # NOTE: e_type always refers to the XML event types for clarity in
    # import script. Database models use etype
    e_type = xmlmap.StringField('@type')
    mepid = xmlmap.StringField('t:p/t:persName/@ref')
    name = xmlmap.StringField('t:p/t:persName')

    # - using StringField to handle decimal values used sometimes
    # catching the issue on the Python side.
    # duration
    duration_unit = xmlmap.StringField('t:p/t:measure[@type="duration"]/@unit')
    duration_quantity = xmlmap.StringField('t:p/t:measure[@type="duration"]/'
                                           '@quantity')
    # frequency
    frequency_unit = xmlmap.IntegerField('t:p/t:measure[@type="frequency"]/@unit')
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

    # reimbursement (another style present with measure type='reimbursement')
    reimbursement_unit = xmlmap.StringField(
        't:p/t:measure[@type="reimbursement"]/@unit'
    )
    reimbursement_quantity = xmlmap.StringField(
        't:p/t:measure[@type="reimbursement"]/@quantity'
    )

    def to_db_event(self, date):

        # Check to see that durations are monthly, if not flag them
        # to test and handle
        if self.duration_unit and self.duration_unit != 'month':
            raise ValueError('Unexpected duration_unit on %s' % date)
        # Map xml events to class names
        xml_db_mapping = {
            'subscription': 'subscribe',
            'supplement': 'subscribe',
            'reimbursement': 'reimbursement',
            'borrow': 'borrow',
            'renewal': 'subscribe'
        }
        # check for unhandled event types
        if self.e_type not in xml_db_mapping:
            raise ValueError('Unexpected e_type on %s' % date)
        etype = xml_db_mapping[self.e_type]
        # Map XML currency to database abbreviations
        xml_currency_mapping = {
            'franc': 'FRF'
        }
        currency = None
        if self.deposit_unit:
            currency = xml_currency_mapping[self.deposit_unit]
        elif self.price_unit:
            currency = xml_currency_mapping[self.price_unit]
        else:
            currency = xml_currency_mapping[self.reimbursement_unit]
        # Get or create person and account
        mep_id = self.mepid.strip('#')
        person = None
        account = None
        person, created = Person.objects.get_or_create(mep_id=mep_id)
        account, created = Account.objects.get_or_create(persons__id=person.id)

        # Create a common dict
        common_dict = {
            'start_date': date,
            'end_date': (date +
                         timedelta(weeks=int(self.duration_quantity) * 4)
                         if self.duration_quantity else date)
        }

        if etype == 'subscribe':
            common_dict['duration'] = self.duration_quantity
            common_dict['volumes'] = self.frequency_quantity
            common_dict['price_paid'] = self.price_quantity
            common_dict['deposit'] = self.deposit_quantity
            common_dict['currency'] = currency

            if self.e_type == 'supplement':
                common_dict['modification'] = Subscribe.SUPPLEMENT
            if self.e_type == 'renewal':
                common_dict['modification'] = Subscribe.RENEWAL

        if etype == 'reimbursement':
            common_dict['price'] = self.price_quantity if self.price_quantity \
                                   else self.reimbursement_quantity
            common_dict['currency'] = currency

        account.persons.add(person)
        account.save()
        account.add_event(etype, **common_dict)


class Day(TeiXmlObject):
    date = xmlmap.DateField('t:head/t:date/@when-iso')
    events = xmlmap.NodeListField('t:listEvent/t:event', XmlEvent)


class LogBook(xmlmap.XmlObject):
    ROOT_NAMESPACES = {
        't': 'http://www.tei-c.org/ns/1.0'
    }

    query = ('//t:body/t:div[@type="year"]/'
             't:div[@type="month"]/t:div[@type="day"]')
    days = xmlmap.NodeListField(query, Day)

    @classmethod
    def from_file(cls, filename):
        return xmlmap.load_xmlobject_from_file(filename, cls)
