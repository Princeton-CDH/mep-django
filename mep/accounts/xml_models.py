# coding=utf-8
import logging
import pendulum
from calendar import monthrange
import re
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from eulxml import xmlmap
from viapy.api import ViafEntity
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
    frequency_unit = xmlmap.StringField('t:p/t:measure[@type="frequency"]/@unit')
    frequency_quantity = xmlmap.IntegerField('t:p/t:measure[@type="frequency"]/'
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

    def _is_int(self, value):
        try:
            int(value)
        except ValueError:
            return False
        return True

    def _normalize_dates(self, common_dict):
        # Check to see that durations are monthly, if not flag them
        # to test and handle
        if self.duration_unit and self.duration_unit not in ['month', 'day']:
            raise ValueError('Unexpected duration_unit on %s' % date)

        # get a pendulum instance for month timedeltas
        pd = pendulum.date.instance(common_dict['start_date'])

        # - simple case
        if self.duration_unit == 'month' and \
                self._is_int(self.duration_quantity):
            common_dict['duration'] = int(self.duration_quantity)
            common_dict['end_date'] = pd.add(months=common_dict['duration'])
        # - duration given as quarter or half
        if self.duration_unit == 'month' and \
                not self._is_int(self.duration_quantity):
            common_dict['duration'] = float(self.duration_quantity)
            # .25 seems to equal one week, or seven days. A half month
            # presumably means to middle of next calendar month, so using 15
            # as nearest approximate
            common_dict['end_date'] = pd.add(
                days=round(common_dict['duration']*29)
            )
        # - duration given as days
        elif self.duration_unit == 'days':
            common_dict['duration'] = float(int(self.duration_quantity) / 28)
            common_dict['end_date'] = pd.add(days=int(self.duration_quantity))
        else:
            common_dict['duration'] = None
            common_dict['end_date'] = None

        return common_dict

    def _normalize(self, e_date):
        '''Return a version of the XMLEvent object with irregularities
        cleaned up.
        :param e_date: Date of event as a `!`
        :type e_date: str.
        :returns: tuple of event type (str.), dict of values for event object,
        :class:`mep.people.models.Person` object, and
        :class:`mep.accounts.models.Account` object.
        '''

        # Create a common dict for base of different event types
        common_dict = {
            'start_date': e_date,
            'notes': '',
        }

        common_dict = self._normalize_dates(common_dict)

        # Map xml events to class names for use with add_event()
        xml_db_mapping = {
            'subscription': 'subscribe',
            'supplement': 'subscribe',
            'reimbursement': 'reimbursement',
            'borrow': 'borrow',
            'renewal': 'subscribe',
            'other': 'event',
        }

        # check for unhandled event types
        if self.e_type not in xml_db_mapping:
            raise ValueError('Unexpected e_type on %s' % date)
        etype = xml_db_mapping[self.e_type]
        # Map XML currency to database abbreviations
        # So far, logbooks seem only to list francs
        xml_currency_mapping = {
            'franc': 'FRF',
        }

        currency = ''
        if self.deposit_unit:
            currency = xml_currency_mapping[self.deposit_unit]
        elif self.price_unit:
            currency = xml_currency_mapping[self.price_unit]
        elif self.reimbursement_unit:
            currency = xml_currency_mapping[self.reimbursement_unit]
        common_dict['currency'] = currency

        # Get or create person and account
        # The logic here handles the accounts that (at least in the logbooks)
        # don't actually include a person to have a mep_id to associate or
        # even a person name.
        mep_id = self.mepid.strip('#') if self.mepid else ''
        person = ''
        account = None
        if not mep_id:
            # Giving these special id's so that they're flagged via ID
            # as it's the only field that isn't a M2M
            account, created = Account.objects.get_or_create(
                id=int(re.sub('-', '', str(e_date)))
            )
            common_dict['notes'] += (
                '!!!Event irregularity!!!\n'
                'No person is associated with this account via <persName>'
            )
        else:
            person, created = Person.objects.get_or_create(mep_id=mep_id)
            if created:
                # Create a stub record if they weren't in the personogoraphy
                # import
                person.name = self.name.strip()
                person.save()
            account, created = Account.objects.get_or_create(
                persons__in=[person]
            )
        return (etype, common_dict, person, account)

    def _parse_subscribe(self, common_dict):
        '''Parse fields from a dictionary for
        :class:`mep.accounts.models.Subscribe` and its sub modifications.'''


        common_dict['volumes'] = self.frequency_quantity
        common_dict['price_paid'] = self.price_quantity
        common_dict['deposit'] = self.deposit_quantity

        if self.e_type == 'subscription' and (not common_dict['duration'] or
                                              not common_dict['price_paid'] or
                                              not common_dict['volumes']):
            common_dict['notes'] += (
                '!!!Event irregularity!!!\n'
                'Duration: %s\n'
                'Volumes: %s\n'
                'Price Paid: %s\n'
                '%s on %s\n'
                'Please check to see if this event can be clarified.\n'
                % (self.duration_quantity, self.frequency_quantity,
                   self.price_quantity, self.mepid, common_dict['start_date'])
            )

            if self.e_type == 'supplement':
                common_dict['modification'] = Subscribe.SUPPLEMENT

            if self.e_type == 'renewal':
                common_dict['modification'] = Subscribe.RENEWAL
        # clear empty keys
        return {k: v for k, v in common_dict.items() if v}

    def to_db_event(self, e_date):
        '''Parse a :class:`XMLEvent` to :class:`mep.accounts.models.Event`
        or subclass.
            :param e_date: A date object representing the event date
            :type e_date: datetime.date
        '''
        # normalize the event
        etype, common_dict, person, account = self._normalize(e_date)
        # This database type encompasses supplements and renewals
        if etype == 'subscribe':
            common_dict = self._parse_subscribe(common_dict)
        # Reimbursement is a subclass that doesn't warrant its own
        # private function
        if etype == 'reimbursement':
            common_dict['price'] = self.price_quantity if self.price_quantity \
                                   else self.reimbursement_quantity
            if not common_dict['price']:
                common_dict['notes'] += (
                    '!!!Event irregularity!!!\n'
                    'Price is missing\n'
                )
        # If there is a person, add them to an account
        if person:
            account.persons.add(person)
            account.save()
        # Call method to create and save the event
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
