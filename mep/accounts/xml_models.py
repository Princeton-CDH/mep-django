# coding=utf-8
import pendulum
import re
from eulxml import xmlmap
from mep.accounts.models import Account, Subscribe
from mep.people.models import Person

class TeiXmlObject(xmlmap.XmlObject):
    ROOT_NAMESPACES = {
        't': 'http://www.tei-c.org/ns/1.0'
    }


class Measure(TeiXmlObject):
    unit = xmlmap.StringField('@unit')
    quantity = xmlmap.StringField('@quantity')

    @staticmethod
    def _is_int(value):
        try:
            int(value)
        except ValueError:
            return False
        return True


class XmlEvent(TeiXmlObject):

    # NOTE: e_type always refers to the XML event types for clarity in
    # import script. Database models use etype
    e_type = xmlmap.StringField('@type')
    mepid = xmlmap.StringField('t:p/t:persName/@ref')
    name = xmlmap.StringField('t:p/t:persName')
    date = xmlmap.DateField('parent::*/parent::*//t:date/@when-iso')
    # - using StringField to handle decimal values used sometimes
    # catching the issue on the Python side.
    # duration
    duration = xmlmap.NodeField('t:p/t:measure[@type="duration"]', Measure)
    frequency = xmlmap.NodeField('t:p/t:measure[@type="frequency"]', Measure)
    price = xmlmap.NodeField('t:p/t:measure[@type="price"]', Measure)
    deposit = xmlmap.NodeField('t:p/t:measure[@type="deposit"]', Measure)
    # reimbursement (another style present with measure type='reimbursement')
    reimbursement = xmlmap.NodeField('t:p/t:measure[@type="reimbursement"]',
                                     Measure)
    sub_type = xmlmap.StringField('t:p/t:rs')
    # common dictionary to use for holding attributes for the Django object
    common_dict = {}

    def _normalize_dates(self):
        '''Return dates in self.common_dict based on xml dates and duration
        quantity.'''
        # get a pendulum instance for month timedeltas
        pd = pendulum.date.instance(self.common_dict['start_date'])
        # - simple case
        if self.duration and self.duration.unit == 'month' and \
                self.duration._is_int(self.duration.quantity):
            self.common_dict['duration'] = int(self.duration.quantity)
            self.common_dict['end_date'] = pd.add(
                months=self.common_dict['duration']
            )
        # - duration given as quarter or half
        elif self.duration and self.duration.unit == 'month' and \
                not self.duration._is_int(self.duration.quantity):
            self.common_dict['duration'] = float(self.duration.quantity)
            # .25 seems to equal one week, or seven days. A half month
            # presumably means to middle of next calendar month, so using 15
            # as nearest approximate
            self.common_dict['end_date'] = pd.add(
                days=round(self.common_dict['duration']*29)
            )
        # - duration given as days
        elif self.duration and self.duration.unit == 'day':
            self.common_dict['duration'] = \
                float(int(self.duration.quantity) / 28)
            self.common_dict['end_date'] = \
                pd.add(days=int(self.duration.quantity))
        else:
            self.common_dict['duration'] = None
            self.common_dict['end_date'] = None

    def _prepare_db_objects(self):
        '''Return a version of the XMLEvent object with irregularities
        in dates and quantities cleaned up and Account and Person objects
        created. Set date, currency, and etype for Django model.
        :returns: tuple of event type (str.), dict of values for event object,
        :class:`mep.people.models.Person` object, and
        :class:`mep.accounts.models.Account` object.
        '''

        # first clean up the dates
        self._normalize_dates()

        # Map xml events to class names for use with add_event()
        xml_db_mapping = {
            'subscription': 'subscribe',
            'supplement': 'subscribe',
            'reimbursement': 'reimbursement',
            'borrow': 'borrow',
            'renewal': 'subscribe',
            'overdue': 'event',
        }

        # check for unhandled event types
        if self.e_type not in xml_db_mapping:
            raise ValueError('Unexpected e_type on %s' % self.date)
        etype = xml_db_mapping[self.e_type]
        # Map XML currency to database abbreviations
        # So far, logbooks seem only to list francs
        xml_currency_mapping = {
            'franc': 'FRF',
        }
        currency = ''
        if self.deposit and self.deposit.unit:
            currency = xml_currency_mapping[self.deposit.unit]
        elif self.price and self.price.unit:
            currency = xml_currency_mapping[self.price.unit]
        elif self.reimbursement and self.reimbursement.unit:
            currency = xml_currency_mapping[self.reimbursement.unit]
        self.common_dict['currency'] = currency

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
                id=int(re.sub('-', '', str(self.date)))
            )
            self.common_dict['notes'] += (
                'Event irregularity\n'
                'No person is associated with this account via <persName>'
            )
        else:
            person, created = Person.objects.get_or_create(mep_id=mep_id)
            if created:
                # Create a stub record if they weren't in the personogoraphy
                # import
                person.name = self.name.strip()
                person.sort_name = self.name.strip()
                person.save()
            account, created = Account.objects.get_or_create(
                persons__in=[person]
            )
            account.persons.add(person)
            # Call method to create and save the event
            account.save()
        return (etype, person, account)

    def _set_subtype(self):
        '''Parse the subtype field for :class:`mep.accounts.models.Subscribe`
        objects from XML to database'''
        sub_type = self.sub_type
        if sub_type:
            # strip periods, parentheses, caps, the word 'and' for ease of
            # sort, lower, and return three letters
            sub_norm = re.sub(r'[.()/\\+\s]|and', '', sub_type.lower())[0:3]
            # mapping for types
            type_map = {
                'adl': Subscribe.ADL,
                'ade': Subscribe.ADL,  # grab A.des. L. and variants
                'stu': Subscribe.STU,
                'st': Subscribe.STU,
                'pr': Subscribe.PROF,
                'pro': Subscribe.PROF,
                'a': Subscribe.A,
                'b': Subscribe.B,
                'ab': Subscribe.A_B,
                # NOTE: Assuming that B + A = A + B for subscription purposes
                'ba': Subscribe.A_B
            }
            if sub_norm in type_map:
                self.common_dict['sub_type'] = type_map[sub_norm]
            else:
                self.common_dict['sub_type'] = Subscribe.OTHER
                self.common_dict['notes'] += ('Unrecognized subscription type:'
                                              ' %s\n' % sub_type.strip())

    def _parse_subscribe(self):
        '''Parse fields from a dictionary for
        :class:`mep.accounts.models.Subscribe` and its sub modifications.'''

        # set fields common to Subscribe variants
        self.common_dict['volumes'] = self.frequency.quantity \
            if self.frequency else None
        self.common_dict['price_paid'] = self.price.quantity \
            if self.price else None
        self.common_dict['deposit'] = self.deposit.quantity \
            if self.deposit else None

        # if date or data are missing so far, note it
        if self.e_type == 'subscription' and \
                (not self.common_dict['duration'] or
                 not self.common_dict['price_paid'] or
                 not self.common_dict['volumes']):

            self.common_dict['notes'] += (
                'Event missing data:\n'
                'Duration: %s\n'
                'Volumes: %s\n'
                'Price Paid: %s\n'
                '%s on %s\n'
                'Please check to see if this event can be clarified.\n'
                % (self.duration.quantity if self.duration else '',
                   self.frequency.quantity if self.frequency else '',
                   self.price.quantity if self.price else '', self.mepid,
                   self.common_dict['start_date'])
            )

        # set modification for supplement and renewal types
        if self.e_type == 'supplement':
            self.common_dict['modification'] = Subscribe.SUPPLEMENT

        if self.e_type == 'renewal':
            self.common_dict['modification'] = Subscribe.RENEWAL

        # set subtype of subscription
        self._set_subtype()

    def to_db_event(self):
        '''Parse a :class:`XMLEvent` to :class:`mep.accounts.models.Event`
        or subclass.
        '''

        # Create a common dict for base of different event types
        self.common_dict = {
            'start_date': self.date,
            'notes': '',
        }

        # normalize the event and prepare Account and Person objs
        etype, person, account = self._prepare_db_objects()
        # This database type encompasses supplements and renewals
        # Handling is complicated and parsed out to _parse_subscribe
        if etype == 'subscribe':
            self._parse_subscribe()
       # Reimbursement is a subclass that doesn't warrant its own
       # private function
        if etype == 'reimbursement':
            self.common_dict['price'] = (self.price.quantity
                                         if self.price and self.price.quantity
                                         else self.reimbursement.quantity if
                                         self.reimbursement else None)
            if not self.common_dict['price']:
                self.common_dict['notes'] += (
                    'Missing price:\n'
                )

        if self.e_type == 'overdue':
            self.common_dict['notes'] += (
                'Overdue notice issued on %s\n'
                'Price: %s %s\n'
                'Duration: %s %ss\n'
                % (self.date, self.price.unit if self.price else '',
                   self.price.quantity if self.price else '',
                   self.duration.quantity if self.duration else '',
                   self.duration.unit if self.duration else '',)
            )
            # not valid for generic events
            self.common_dict['currency'] = None
            self.common_dict['duration'] = None

        # drop blank keys from dict to avoid passing a bad kwarg to a model
        account.add_event(etype, **{key: value
                          for key, value in self.common_dict.items() if value})


class LogBook(xmlmap.XmlObject):
    ROOT_NAMESPACES = {
        't': 'http://www.tei-c.org/ns/1.0'
    }

    query = ('//t:event')
    events = xmlmap.NodeListField(query, XmlEvent)

    @classmethod
    def from_file(cls, filename):
        return xmlmap.load_xmlobject_from_file(filename, cls)
