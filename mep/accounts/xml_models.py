# coding=utf-8
import re

from cached_property import cached_property
from eulxml import xmlmap
import pendulum

from mep.accounts.models import Account, Subscription, SubscriptionType, \
    Borrow
from mep.books.models import Item
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
            'subscription': 'subscription',
            'supplement': 'subscription',
            'reimbursement': 'reimbursement',
            'borrow': 'borrow',
            'renewal': 'subscription',
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
            account = Account.objects.create()
            self.common_dict['notes'] += (
                'Event irregularity\n'
                'No person is associated with this account via mepid.\n'
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

    # subscription type lookup
    @cached_property
    def subscription_type(self):
        subscription_type = {
            'adl': SubscriptionType.objects.get(name='AdL'),
            'stu': SubscriptionType.objects.get(name='Student'),
            'pr': SubscriptionType.objects.get(name='Professor'),
            'a': SubscriptionType.objects.get(name='A'),
            'b': SubscriptionType.objects.get(name='B'),
            'ab': SubscriptionType.objects.get(name='A+B'),
            'other': SubscriptionType.objects.get(name='Other'),
        }
        # variant codes that map to above types
        subscription_type['ade'] = subscription_type['adl']
        subscription_type['st'] = subscription_type['stu']
        subscription_type['pro'] = subscription_type['pr']
        # NOTE: Assuming that B + A = A + B for subscription purposes
        subscription_type['ba'] = subscription_type['ab']
        return subscription_type

    def _set_subtype(self):
        '''Parse the subtype field for :class:`mep.accounts.models.Subscription`
        objects from XML to database'''
        sub_type = self.sub_type
        if sub_type:
            # strip periods, parentheses, caps, the word 'and' for ease of
            # sort, lower, and return three letters
            sub_norm = re.sub(r'[.()/\\+\s]|and', '', sub_type.lower())[0:3]

            if sub_norm in self.subscription_type:
                self.common_dict['category'] = self.subscription_type[sub_norm]
            else:
                self.common_dict['category'] = self.subscription_type['other']
                self.common_dict['notes'] += ('Unrecognized subscription type:'
                                              ' %s\n' % sub_type.strip())

    def _parse_subscription(self):
        '''Parse fields from a dictionary for
        :class:`mep.accounts.models.Subscription` and its variant types.'''

        # set fields common to Subscription variants
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
                'Subscription missing data:\n'
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

        # set type for supplement and renewal types
        if self.e_type == 'supplement':
            self.common_dict['subtype'] = Subscription.SUPPLEMENT

        if self.e_type == 'renewal':
            self.common_dict['subtype'] = Subscription.RENEWAL

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
        # Handling is complicated and parsed out to _parse_subscription
        if etype == 'subscription':
            self._parse_subscription()
       # Reimbursement is a subclass that doesn't warrant its own
       # private function
        if etype == 'reimbursement':
            self.common_dict['refund'] = (self.price.quantity
                                         if self.price and self.price.quantity
                                         else self.reimbursement.quantity if
                                         self.reimbursement else None)
            if not self.common_dict['refund']:
                self.common_dict['notes'] += (
                    'Missing price\n'
                )

        if self.e_type == 'overdue':
            self.common_dict['notes'] += (
                'Overdue notice issued on %s\n'
                'Price: %s %s\n'
                'Duration: %s %s\n'
                % (self.date, self.price.unit if self.price else '',
                   self.price.quantity if self.price else '',
                   self.duration.quantity if self.duration else '',
                   self.duration.unit if self.duration else '',)
            )
            # not valid for generic events
            self.common_dict['currency'] = None
            self.common_dict['duration'] = None

        # drop blank values from dict to avoid passing a bad kwarg to a model
        account.add_event(etype, **{key: value
                          for key, value in self.common_dict.items() if value})


class LogBook(TeiXmlObject):

    query = ('//t:event')
    events = xmlmap.NodeListField(query, XmlEvent)

    @classmethod
    def from_file(cls, filename):
        return xmlmap.load_xmlobject_from_file(filename, cls)


## lending cards and borrowing events

class BorrowedItem(TeiXmlObject):
    '''an item within a borrowing event; may just have a title'''
    title = xmlmap.StringField('t:title')
    author = xmlmap.StringField('t:author')
    mep_id = xmlmap.StringField('@corresp')



class BorrowingEvent(TeiXmlObject):
    '''a record of a borrowing event; item with check out and return date'''
    checked_out = xmlmap.DateField('t:date[@ana="#checkedOut"]/@when')
    returned = xmlmap.DateField('t:date[@ana="#returned"]/@when')
    item = xmlmap.NodeField('t:bibl[@ana="#borrowedItem"]', BorrowedItem)

    def to_db_event(self, account):
        borrow = Borrow(account=account, start_date=self.checked_out,
            end_date=self.returned)
        # find item that was borrowed
        # *should* already exist from regularized title import
        borrow.item =  Item.objects.get(mep_id=self.item.mep_id)
        # TODO: add author if present here and not on item (?)
        return borrow


class LendingCard(TeiXmlObject):
    # TODO: person, card images, etc

    # use person name with card holder rolelrderand id in the header to identify card holder
    cardholder = xmlmap.StringField('//t:person[@role="cardholder"]')
    cardholder_id = xmlmap.StringField('substring-after(//t:person[@role="cardholder"]/@ana, "#")')

    # find borroqwing events anywhere in the document
    borrowing_events = xmlmap.NodeListField('//t:ab[@ana="#borrowingEvent"]',
        BorrowingEvent)


# custom xml generated by previous project tech lead with
# regularized title information

class BorrowedTitle(xmlmap.XmlObject):
    mep_id = xmlmap.StringField('titleid')
    title =  xmlmap.StringField('regularized_title', normalize=True)
    unreg_title =  xmlmap.StringField('title', normalize=True)


class BorrowedTitles(xmlmap.XmlObject):
    titles = xmlmap.NodeListField('row', BorrowedTitle)



