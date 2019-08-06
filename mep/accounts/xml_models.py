# coding=utf-8
import re

from cached_property import cached_property
from eulxml import xmlmap
from lxml.etree import cleanup_namespaces
import pendulum


from mep.accounts.models import Account, Subscription, SubscriptionType, \
    Borrow
from mep.accounts.partial_date import DatePrecision
from mep.books.models import Work
from mep.people.models import Person


class TeiXmlObject(xmlmap.XmlObject):
    ROOT_NAMESPACES = {
        't': 'http://www.tei-c.org/ns/1.0'
    }

    def serialize_no_ns(self):
        # convenience function to serialize xml and strip out TEI
        # namespace declaration for brevity in database notes
        # remove any unused namespaces before serializing
        cleanup_namespaces(self.node.getroottree())
        # strip out tei namespace declaration after serializing
        return self.serialize(pretty=True).decode('utf-8') \
            .replace(' xmlns="%s"' % self.ROOT_NAMESPACES['t'], '')


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


class BibliographicScope(TeiXmlObject):
    unit = xmlmap.StringField('@unit')
    text = xmlmap.StringField('text()')

    @property
    def label(self):
        # label for this scope; use unit attribute if present,
        # otherwise use tag name (i.e. for edition)
        return self.unit or \
            self.node.tag.replace('{%s}' % self.ROOT_NAMESPACES['t'], '')


class BorrowedItemTitle(TeiXmlObject):
    #: contains an unclear tag
    is_unclear = xmlmap.NodeField('t:unclear', TeiXmlObject)

    def __str__(self):
        # customize string method to include marker for <unclear/>
        content = [self.node.text or '']
        for node in self.node:
            if node.tag == '{http://www.tei-c.org/ns/1.0}unclear':
                content.append('[unclear]')
            content.append(node.text or '')
            content.append(node.tail or '')

        if content:
            return ''.join(content)


class BorrowedItem(TeiXmlObject):
    '''an item within a borrowing event; may just have a title'''
    title = xmlmap.NodeField('t:title', BorrowedItemTitle)
    author = xmlmap.StringField('t:author')
    mep_id = xmlmap.StringField('@corresp')
    publisher = xmlmap.StringField('t:publisher')
    date = xmlmap.StringField('t:date')
    scope_list = xmlmap.NodeListField('t:biblScope|t:edition', BibliographicScope)


class BorrowDate(TeiXmlObject):
    # NOTE: mapping when date as string instead of DateTime because
    # dates are not always complete; date parsing handled by PartialDate
    when = xmlmap.StringField('@when')
    # not before/after always full ISO date
    not_before = xmlmap.DateField('@notBefore')
    not_after = xmlmap.DateField('@notAfter')

class BorrowingEvent(TeiXmlObject):
    '''a record of a borrowing event; item with check out and return date'''
    checked_out = xmlmap.NodeField('t:date[@ana="#checkedOut"]', BorrowDate)
    returned = xmlmap.NodeField('t:date[@ana="#returned"]', BorrowDate)
    # bibl could be directly in the event <ab> tag _or_ within a <del>
    item = xmlmap.NodeField('.//t:bibl[@ana="#borrowedItem"]', BorrowedItem)
    notes = xmlmap.StringField('t:note')

    #: crossed out text anywhere within the borrowing event
    deletions = xmlmap.NodeListField('.//t:del', TeiXmlObject)
    #: dates that aren't tagged as checked out or returned
    extra_dates = xmlmap.NodeListField('t:date[not(@ana="#returned" or @ana="#checkedOut")]',
        TeiXmlObject)

    @property
    def bought(self):
        '''item was bought, based on text note ('BB', 'bought', 'to buy', etc)'''
        # list of known terms in notes that indicate a book was bought
        bought_terms = ['BB', 'B B', 'B.B.', 'bought', 'Bought', 'to buy']
        return bool(self.notes) and \
            any([bought in self.notes for bought in bought_terms])

    @property
    def returned_note(self):
        '''notes indicate item was returned even though there is no return date'''
        return_terms = ['return', 'returned', 'back']
        return bool(self.notes) and \
            any([ret in self.notes for ret in return_terms])

    # generic titles that should *not* be aggregated together in spite
    # of shared mep id, because these are almost certainly not the same work
    # in all cases
    GENERIC_TITLES = [
        "Theatre", "Oscar Wilde", "James Joyce", "Blake",
        "Shakespeare", "Tennyson", "Selected Poems", "Chaucer",
        "Swinburne", "Hamlet", "Shelley", '"', "John Donne", "Trumpet major",
        "D.H. Lawrence", "Coleridge", "Autobiography", "Hist. of England",
        "English novel", "Hart Crane", "Irish Drama", "Letters", "Napoleon",
        "William Blake", "Coll. Poems", "New Poetry", "Charls Dickens",
        "C.", "American History 2", "Queen Elizabeth", "Life of Shakespeare",
        "Walter Pater", "Mozart", "Dostoevsky", "[unclear]", "Edgar Allen Poe",
        "Conrad", "Life of Oscar Wilde", "Meredith", "Dramatic Works",
        "A.C. Swinburne", "Beethoven", "Poetry and Prose", "Memoirs",
        "Poems and Plays", "Complete Poems", "Poetical Works", "Emerson",
        "Life and Writings", "Poems", "Collected Poems", "Plays", "Essays",
        "Three Plays"
    ]

    # MEP title id based on generic titles above
    GENERIC_TITLE_IDS = [
        "mep:00060b", "mep:00071x", "mep:000q6b", "mep:000v26", "mep:001106",
        "mep:00128z", "mep:00137x", "mep:00181f", "mep:001w8k", "mep:001x1p",
        "mep:00242w", "mep:002d6b", "mep:002p29", "mep:00428p", "mep:004440",
        "mep:00470k", "mep:00480v", "mep:00486q", "mep:004w6p", "mep:005q4x",
        "mep:006s0g", "mep:006w93", "mep:007184", "mep:007915", "mep:009357",
        "mep:009t6b", "mep:00b21z", "mep:00b53d", "mep:00bc60", "mep:00bh5s",
        "mep:00bk0s", "mep:00c34d", "mep:00c511", "mep:00c69s", "mep:00cf5g",
        "mep:00cf6s", "mep:00d902", "mep:00dj00", "mep:00f81b", "mep:00g47b",
        "mep:00g597", "mep:00hb2p", "mep:00j76b", "mep:00k650", "mep:00qm2b",
        "mep:swinburnenicholson", "mep:000z0d",
        # multiple ids for poems:
        "mep:00kb81", "mep:00209z", "mep:00jd5d", "mep:009f7m", "mep:00t00g",
        "mep:001n61",
        # multiple ids for collected poems:
        "mep:001565", "mep:00rr77", "mep:007p72", "mep:00546v", "mep:002h8s",
        # multiple ids for plays:
        "mep:00dv4q", "mep:00g227", "mep:000s1b",
        # multiple ids for three plays:
        "mep:004q8x", "mep:007k9v"
    ]

    def to_db_event(self, account):
        '''Generate a database :class:`~mep.accounts.models.Borrow` event
        for the current xml borrowing event.'''

        borrow = Borrow(account=account)
        # array to gather notes
        notes = []

        if self.checked_out:
            borrow.calculate_date('start_date', self.checked_out.when,
                self.checked_out.not_before, self.checked_out.not_after)

            # document not before/after in notes when appropriate
            if not self.checked_out.when and self.checked_out.not_before \
              and self.checked_out.not_after:
                notes.append('checked out between %s / %s' % \
                             (self.checked_out.not_before,
                              self.checked_out.not_after))

        if self.returned:
            borrow.calculate_date('end_date', self.returned.when,
                self.returned.not_before, self.returned.not_after)

            # document not before/after in notes when appropriate
            if not self.returned.when and self.returned.not_before \
              and self.returned.not_after:
                notes.append('returned between %s / %s' % \
                             (self.returned.not_before,
                              self.returned.not_after))

        # set item status if possible
        # if there is a return date, item was returned
        if self.returned:
            borrow.item_status = Borrow.ITEM_RETURNED
        else:
            # set status to bought or returned if the notes indicate it
            if self.bought:
                borrow.item_status = Borrow.ITEM_BOUGHT
            elif self.returned_note:
                borrow.item_status = Borrow.ITEM_RETURNED

        # if we have an mep id and it is not flagged as a generic id
        # that should not be aggregated, find the existing item record
        if self.item.mep_id and self.item.mep_id not in self.GENERIC_TITLE_IDS:
            # find item that was borrowed
            # *should* already exist from regularized title import;
            # if item does not exist, create a new stub record
            borrow.item, created = Work.objects.get_or_create(mep_id=self.item.mep_id)

        # if no mep id or a generic id, create a new record
        else:
            # NOTE: some records have an unclear title or partially unclear title
            #  with no mep id for the item
            borrow.item = Work.objects.create()
            created = True

        # if item was newly created OR borrow title is unclear, set the title
        if created or self.item.title and self.item.title.is_unclear:
            # some borrowing events have an author and no title
            borrow.item.title = self.item.title or '[no title]'

        # if bibliographic details are present, document them in the item note
        # to support book title data work
        bibl_info = []
        if self.item.author and self.item.author not in borrow.item.notes:
            bibl_info.append('Author: %s' % self.item.author)
        if self.item.publisher and self.item.publisher not in borrow.item.notes:
            bibl_info.append('Publisher: %s' % self.item.publisher)
        if self.item.date and self.item.date not in borrow.item.notes:
            bibl_info.append('Date: %s' % self.item.date)

        if bibl_info:
            borrow.item.notes += '\n'.join(bibl_info)

        # save the item if it is new or notes were added
        if bibl_info or created:
            borrow.item.save()

        # gather information to be included in borrowing events notes

        # include text inside <note> tag in the xml
        if self.notes:
            notes.append(self.notes)
        # include xml for any <del> tags
        for deleted_text in self.deletions:
            notes.append(deleted_text.serialize_no_ns())
        # untagged dates (could be a missed return date or similar)
        for extra_date in self.extra_dates:
            notes.append(extra_date.serialize_no_ns())

        # bibliographic scope seems to be particular to this borrowing
        # event rather than the title, so adding here
        for bibl_scope in self.item.scope_list:
            # e.g. number/issue and any text...
            notes.append('%s %s' % (bibl_scope.label, bibl_scope.text))

        borrow.notes = '\n'.join(notes)

        return borrow

class Cardholder(TeiXmlObject):
    name = xmlmap.StringField('.', normalize=True)
    # persName with cardholder role uses ana; persname in head uses ref
    mep_id = xmlmap.StringField('substring-after(concat(@ana, @ref), "#")')


class FacsimileSurface(TeiXmlObject):
    xml_id = xmlmap.StringField('@xml:id')
    url = xmlmap.StringField('t:graphic/@url')


class LendingCardSide(TeiXmlObject):
    '''A single side of a lending card'''
    #: id for the image that represents this page
    facsimile_id = xmlmap.StringField('substring-after(t:pb/@facs, "#")')
    #: any borrowing events on this card
    borrowing_events = xmlmap.NodeListField('.//t:ab[@ana="#borrowingEvent"]',
        BorrowingEvent)
    #: the card holder for this page should be the *first* person listed
    cardholders = xmlmap.NodeListField('t:head/t:persName[@ana or @ref]', Cardholder)


class LendingCard(TeiXmlObject):

    # use person element with card holder role to identify card holder
    # could be multiple; allow for organization as well as person
    cardholders = xmlmap.NodeListField('//t:person[@role="cardholder"]|//t:org[@role="cardholder"]',
        Cardholder)

    # all borrowing events anywhere in the document
    borrowing_events = xmlmap.NodeListField('//t:ab[@ana="#borrowingEvent"]',
        BorrowingEvent)

    image_base_path = xmlmap.StringField('t:facsimile/@xml:base')
    # surface could be inside a surface group (e.g. alvear includes an envelope and a letter)
    surfaces = xmlmap.NodeListField('t:facsimile//t:surface', FacsimileSurface)

    sides = xmlmap.NodeListField('//t:div[@type="card"]/t:div', LendingCardSide)

    @property
    def surface_by_id(self):
        # too bad eulxml never got a dictfield type...
        return {surf.xml_id: surf.url for surf in self.surfaces}

    def image_path(self, image_id):
        return ''.join([self.image_base_path, self.surface_by_id[image_id]])


# custom xml generated by previous project tech lead with
# regularized title information
class BorrowedTitle(xmlmap.XmlObject):
    mep_id = xmlmap.StringField('titleid')
    title = xmlmap.StringField('regularized_title', normalize=True)
    unreg_title = xmlmap.StringField('title', normalize=True)


class BorrowedTitles(xmlmap.XmlObject):
    titles = xmlmap.NodeListField('row', BorrowedTitle)
