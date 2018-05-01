import datetime
import os

from django.test import TestCase
from eulxml import xmlmap

from mep.accounts.xml_models import LogBook, Measure, BorrowedItem, \
    BorrowingEvent, LendingCard, BorrowedTitle, BorrowedTitles, \
    BorrowedItemTitle, FacsimileSurface, LendingCardSide
from mep.accounts.models import Event, Subscription, Reimbursement, Account, \
    CurrencyMixin, Borrow
from mep.books.models import Item
from mep.people.models import Person


FIXTURE_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'fixtures'
)
XML_FIXTURE = os.path.join(FIXTURE_DIR, 'sample-logbook.xml')


class TestLogbook(TestCase):

    def test_from_file(self):
        logbook = LogBook.from_file(XML_FIXTURE)
        assert isinstance(logbook, LogBook)
        # Nine sample events included
        assert len(logbook.events) == 11


class TestEvent(TestCase):

    def setUp(self):
        self.logbook = LogBook.from_file(XML_FIXTURE)

    def test_attributes(self):
        monbrial = self.logbook.events[0]
        assert monbrial.e_type == 'subscription'
        assert monbrial.date == datetime.date(1921, 1, 5)
        assert monbrial.mepid == '#monb'
        assert monbrial.name == 'Mlle Monbrial'
        assert monbrial.duration.unit == 'month'
        assert monbrial.duration.quantity == '3'
        assert monbrial.frequency.unit == 'volume'
        assert monbrial.frequency.quantity == '1'
        assert monbrial.price.unit == 'franc'
        assert monbrial.price.quantity == '16'
        assert monbrial.deposit.unit == 'franc'
        assert monbrial.deposit.quantity == '7'
        assert not monbrial.sub_type

        for event in self.logbook.events:
            event.to_db_event()
        # check that there are 11 events overall
        events = Event.objects.all()
        assert len(events) == 11

        # check that there are 7 subscribes
        subscribes = Subscription.objects.all()
        assert len(subscribes) == 7

        # check one in detail
        monbrial = subscribes.filter(account__persons__mep_id='monb')[0]
        assert monbrial.start_date == datetime.date(1921, 1, 5)
        assert monbrial.end_date == datetime.date(1921, 4, 5)
        assert monbrial.duration == 90
        assert monbrial.currency == CurrencyMixin.FRF
        assert monbrial.deposit == 7
        assert monbrial.price_paid == 16

        # check the reimbursement because it's different enough
        kunst = Reimbursement.objects.get(account__persons__mep_id__icontains='kunst')
        assert kunst.start_date == datetime.date(1921, 1, 5)
        # single day event - end date = start date
        assert kunst.end_date == kunst.start_date
        assert kunst.currency == CurrencyMixin.FRF
        assert kunst.refund == 200

        # check reimbursements that use <measure type="reimbursement" ... >
        burning = Reimbursement.objects.get(account__persons__mep_id__icontains='burning')
        assert burning.currency == CurrencyMixin.FRF
        assert burning.refund == 50

        # make sure a missing price is noted
        foobar = Reimbursement.objects.get(account__persons__mep_id__icontains='foo')
        assert not foobar.refund
        assert 'Missing price' in foobar.notes

        # check a subscription that should have a subclass
        # there should be one in the fixture and its mep_id should be declos
        declos = Subscription.objects.filter(category__name='AdL').first()
        assert declos
        assert declos.account.persons.first().mep_id == 'desc.au'

        # check overdue notice parsing
        loomis = Event.objects.filter(notes__icontains='overdue')[0]
        assert 'Overdue notice' in loomis.notes
        assert 'issued on 1921-01-08' in loomis.notes
        assert 'franc 60' in loomis.notes
        assert '3 month' in loomis.notes

        # also check anonymous account handling
        assert loomis.account
        assert 'Event irregularity\n' in loomis.notes
        assert 'No person is associated with this account via mepid.\n' in loomis.notes

    def test__is_int(self):
        assert Measure._is_int("7")
        assert not Measure._is_int("foobar")

    def test__prepare_db_objects(self):
        monbrial = self.logbook.events[0]
        # fake first step of _normalize to test normalize db prep independently
        monbrial.common_dict = {
            'start_date': monbrial.date,
            'notes': '',
        }
        # - test basic functionality on a standard subscribe
        etype, person, account = monbrial._prepare_db_objects()

        # should have set type for django database
        assert etype == 'subscription'
        assert monbrial.common_dict == {
            'currency': CurrencyMixin.FRF,
            'notes': '',
            'duration': 3,
            'start_date': datetime.date(1921, 1, 5),
            'end_date': datetime.date(1921, 4, 5),
        }

        # should have created a person stub and an associated account
        assert person == Person.objects.get(mep_id='monb')
        assert account == Account.objects.get(persons__in=[person])

        # unknown e_type should raise a ValueError
        monbrial.e_type = 'foobar'
        with self.assertRaises(ValueError):
            monbrial._prepare_db_objects()

    def test__parse_subscription(self):
        monbrial = self.logbook.events[0]

        # fake first step of _normalize to test normalize dates independently
        monbrial.common_dict = {
            'start_date': monbrial.date,
            'notes': '',
        }

        # - test with a standard subscription
        monbrial._prepare_db_objects()
        monbrial._parse_subscription()
        common_dict = monbrial.common_dict

        # should have set keys
        assert 'volumes' in common_dict
        assert 'price_paid' in common_dict
        assert 'deposit' in common_dict
        assert 'event_type' not in common_dict

        # values pulled from XML correctly
        assert int(common_dict['volumes']) == 1
        assert int(common_dict['price_paid']) == 16
        assert float(common_dict['deposit']) == 7

        # - test handling for missing quantities, etc.
        monbrial.frequency.quantity = None
        monbrial._parse_subscription()
        assert 'Subscription missing data:\n' in monbrial.common_dict['notes']
        assert 'Volumes: None' in monbrial.common_dict['notes']
        assert 'Duration: 3' in monbrial.common_dict['notes']
        assert 'Price Paid: 16' in monbrial.common_dict['notes']
        # now the rest also need to be cleared to make sure note logic works
        monbrial.price.quantity = None
        monbrial.deposit.quantity = None
        monbrial.duration.quantity = None
        monbrial._parse_subscription()
        assert 'Duration: None' in monbrial.common_dict['notes']
        assert 'Price Paid: None' in monbrial.common_dict['notes']
        assert '#monb on 1921-01-05' in monbrial.common_dict['notes']

    def test__set_subtype(self):
        # - basic event, no subtype
        monbrial = self.logbook.events[0]
        # fake first step of _normalize to test subtype independently
        monbrial.common_dict = {
            'start_date': monbrial.date,
            'notes': '',
        }
        monbrial._prepare_db_objects()
        monbrial._set_subtype()
        assert 'sub_type' not in monbrial.common_dict
        # - add sub_type
        monbrial.sub_type = 'A.d.c'
        monbrial._set_subtype()
        assert monbrial.common_dict['category'].name == 'Other'

        # - test sub_types comprehensively using variations from the MEP report
        stu = ['(stud.)', 'Student', '(Stud)', 'st', 'St.', '/ Stud/']
        for var in stu:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['category'].name == 'Student'

        prof = ['Professor', 'Prof', 'Pr', '(Prof.)']
        for var in prof:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['category'].name == 'Professor'

        a = ['A', 'A.', 'a']
        for var in a:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['category'].name == 'A'

        b = ['B', 'B.', 'b']
        for var in b:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['category'].name == 'B'

        ab = ['B+A', 'A + B', 'B + A', 'a and b', 'A and B']
        for var in ab:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['category'].name == 'A+B'

        adl = ['A.des.l', 'ADL', 'A. d. L.', 'AdL']
        for var in adl:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['category'].name == 'AdL'

        other = ['D.D.', 'A.S.L', 'foo', 'bar']
        for var in other:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['category'].name == 'Other'
            assert 'Unrecognized subscription type: %s' % var \
                in monbrial.common_dict['notes']

    def test__normalize_dates(self):

        monbrial = self.logbook.events[0]
        # fake first step of _normalize to test normalize dates independently
        monbrial.common_dict = {
            'start_date': monbrial.date,
            'notes': '',
        }
        monbrial._normalize_dates()
        # should show a three month interval
        assert monbrial.common_dict['start_date'] == datetime.date(1921, 1, 5)
        assert monbrial.common_dict['end_date'] == datetime.date(1921, 4, 5)

        # make the duration quantity one
        monbrial.duration.quantity = 1
        monbrial._normalize_dates()
        assert monbrial.common_dict['end_date'] == datetime.date(1921, 2, 5)

        # - test float variation cases
        monbrial.duration.quantity = '.25'
        monbrial._normalize_dates()
        assert monbrial.common_dict['end_date'] == datetime.date(1921, 1, 12)

        monbrial.duration.quantity = '.5'
        monbrial._normalize_dates()
        assert monbrial.common_dict['end_date'] == datetime.date(1921, 1, 19)

        # - duration given in days
        monbrial.duration.quantity = '7'
        monbrial.duration.unit = 'day'
        monbrial._normalize_dates()
        assert monbrial.common_dict['end_date'] == datetime.date(1921, 1, 12)


class TestBorrowedItem(TestCase):

    def test_fields(self):
        # simple example, title only
        item = xmlmap.load_xmlobject_from_string('''<bibl xmlns="http://www.tei-c.org/ns/1.0"
            ana="#borrowedItem"><title>Poets Two Painters</title></bibl>''',
            BorrowedItem)
        assert str(item.title) == 'Poets Two Painters'
        assert not item.author
        assert not item.mep_id

        # full example with author and mep id
        item = xmlmap.load_xmlobject_from_string('''<bibl xmlns="http://www.tei-c.org/ns/1.0"
            corresp="mep:00018f"><title>Spider Boy</title> <author>C. Van Vechten</author></bibl>''',
            BorrowedItem)
        assert str(item.title) == 'Spider Boy'
        assert item.author == 'C. Van Vechten'
        assert item.mep_id == 'mep:00018f'


class TestBorrowedItemTitle(TestCase):

    text_title = '<title>Poets Two Painters</title>'
    unclear_title = '<title xmlns="http://www.tei-c.org/ns/1.0"><unclear/></title>'
    partially_unclear = '<title xmlns="http://www.tei-c.org/ns/1.0"><unclear/> of Man</title>'

    def test_str(self):
        # text only
        title = xmlmap.load_xmlobject_from_string(self.text_title,
            BorrowedItemTitle)
        assert str(title) == 'Poets Two Painters'

        # totally unclear
        title = xmlmap.load_xmlobject_from_string(self.unclear_title,
            BorrowedItemTitle)
        assert str(title) == '[unclear]'

        # partially unclear
        title = xmlmap.load_xmlobject_from_string(self.partially_unclear,
            BorrowedItemTitle)
        assert str(title) == '[unclear] of Man'

    def test_unclear(self):
        # text only
        title = xmlmap.load_xmlobject_from_string(self.text_title,
            BorrowedItemTitle)
        assert not title.is_unclear

        # totally unclear
        title = xmlmap.load_xmlobject_from_string(self.unclear_title,
            BorrowedItemTitle)
        assert title.is_unclear

        # partially unclear
        title = xmlmap.load_xmlobject_from_string(self.partially_unclear,
            BorrowedItemTitle)
        assert title.is_unclear


class TestBorrowingEvent(TestCase):

    two_painters = '''<ab xmlns="http://www.tei-c.org/ns/1.0"
        ana="#borrowingEvent">
          <date ana="#checkedOut" when="1939-04-06">Apr 6</date>
           <bibl ana="#borrowedItem" corresp="mep:006866"><title>Poets Two Painters</title></bibl>
           <date ana="#returned" when="1939-04-13">Apr 13</date>
           <note>2v pd.</note>
        </ab>'''
    tromolt = '''<ab xmlns="http://www.tei-c.org/ns/1.0"
        ana="#borrowingEvent">
            <date ana="#checkedOut" when="1934-02-10">Feb 10</date>
            <del>
                <bibl ana="#borrowedItem" corresp="mep:00jd71">
                    <title>Wife of Steffan Tromholt</title>
                    <biblScope unit="volume" from="1" to="2">2 vols</biblScope>
                </bibl>
            </del>
        </ab>'''
    partial_date = '''<ab xmlns="http://www.tei-c.org/ns/1.0" ana="#borrowingEvent">
        <date ana="#checkedOut" when="1956-01">Jan</date>
       <bibl ana="#borrowedItem" corresp="mep:000j03"> <title>Toussaint Louverture</title>, <author>Michel Vaucaire</author></bibl>
       <date ana="#returned" when="1956-04-01"></date>
    </ab>'''

    bought = '''<ab xmlns="http://www.tei-c.org/ns/1.0" ana="#borrowingEvent">
        <date ana="#checkedOut" when="1921-05-28">  </date>
        <bibl ana="#borrowedItem" corresp="mep:000v26"><title>Blake</title>
            (<publisher> "  </publisher>)</bibl>
        <note>BB</note>
    </ab>'''

    del_text = '''<ab xmlns="http://www.tei-c.org/ns/1.0" ana="#borrowingEvent">
        <date ana="#checkedOut" when="1936-02-12">Feb. 12.</date>
        <del>
         <bibl corresp="mep:000r7x">Wast</bibl>
      </del>
        <bibl ana="#borrowedItem" corresp="mep:000r6m">
            <title>How to Read</title>
        </bibl>
        <note>... 2.50. Pd.</note>
        <date ana="#returned" when="1936-03-07">March 7</date>
      </ab>'''

    extra_dates = '''<ab xmlns="http://www.tei-c.org/ns/1.0" ana="#borrowingEvent">
        (<bibl ana="#borrowedItem" corresp="mep:000b97">
            <title>Holy Mountain</title>
         </bibl>
         <date when="1938-02-11">Feb 11 1938</date>)
      <date when="1938-12-27">Dec 27</date>
      </ab>'''

    bibl_pub_date = '''<ab xmlns="http://www.tei-c.org/ns/1.0" ana="#borrowingEvent">
          <date ana="#checkedOut" when="1947-02-20"/>
          <bibl ana="#borrowedItem" corresp="mep:00mz7x">
            <title>Early Memories: some chapters of autobiography</title>
            <author>W.B. Yeats</author>
            <publisher>Cuala Press</publisher>
            <date when="1923">1923</date>
          </bibl>
          <date ana="#returned" when="1947-03-29">"</date>
        </ab>'''

    biblscope = '''<ab xmlns="http://www.tei-c.org/ns/1.0" ana="#borrowingEvent">
          <date ana="#checkedOut" when="1947-02-20">Feb 20</date>
          <bibl ana="#borrowedItem" corresp="mep:002h1m">
            <title>Hound &amp; Horn</title>
            <biblScope unit="number">(Henry James No</biblScope>
            <biblScope unit="issue">April - May 1934</biblScope>
          </bibl>
          <date ana="#returned" when="1947-03-29">March 29</date>
        </ab>'''

    no_title = '''<ab xmlns="http://www.tei-c.org/ns/1.0" ana="#borrowingEvent">
          <date ana="#checkedOut" when="1936-05-08">May 8</date>
          <bibl ana="#borrowedItem">
         <author>T.E. Lawrence</author>
      </bibl>
          <date ana="#returned" when="1936-05-14">"   14</date>
        </ab>'''

    edition = '''<ab xmlns="http://www.tei-c.org/ns/1.0" ana="#borrowingEvent">
        <date ana="#checkedOut" when="1939-05-06"/>
        <bibl ana="#borrowedItem" corresp="mep:009q7t">
            <biblScope unit="volume" from="2">Vol 2.</biblScope>
            <edition>Everyman</edition>
        </bibl>
        <date ana="#returned" when="1939-07-18">July 18</date>
      </ab>'''

    def test_fields(self):
        event = xmlmap.load_xmlobject_from_string(self.two_painters,
            BorrowingEvent)

        assert event.checked_out == '1939-04-06'
        assert event.returned == '1939-04-13'
        assert isinstance(event.item, BorrowedItem)
        assert str(event.item.title) == 'Poets Two Painters'
        assert event.item.mep_id == 'mep:006866'

        # bibl inside a <del>
        event = xmlmap.load_xmlobject_from_string(self.tromolt, BorrowingEvent)
        assert str(event.item.title) == 'Wife of Steffan Tromholt'
        # biblscope?

        # notes
        event = xmlmap.load_xmlobject_from_string(self.bought, BorrowingEvent)
        assert event.notes == 'BB'

    def test_bought(self):
        # no bought flag in notes
        event = xmlmap.load_xmlobject_from_string(self.tromolt, BorrowingEvent)
        assert event.bought is False

        # bought flag in notes - variant one
        event = xmlmap.load_xmlobject_from_string(self.bought, BorrowingEvent)
        assert event.bought

        # variant texts that should also be recognized
        event.notes = 'bought book'
        assert event.bought
        event.notes = 'BB'
        assert event.bought
        event.notes = 'B B'
        assert event.bought
        event.notes = 'B.B.'
        assert event.bought
        event.notes = 'to buy'
        assert event.bought

    def test_returned_note(self):
        # no returned flag in notes
        event = xmlmap.load_xmlobject_from_string(self.tromolt, BorrowingEvent)
        assert event.returned_note is False

        # returned flag in notes
        event.notes = 'returned'
        assert event.returned_note
        event.notes = 'back'
        assert event.returned_note

    def test_to_db_event(self):
        xmlevent = xmlmap.load_xmlobject_from_string(self.two_painters,
                                                     BorrowingEvent)
        account = Account()
        # create stub title record - should be used if present
        poets = Item.objects.create(mep_id='mep:006866', title="Poets Two Painters")
        db_borrow = xmlevent.to_db_event(account)
        assert isinstance(db_borrow, Borrow)
        assert db_borrow.account == account
        assert db_borrow.item_status == Borrow.ITEM_RETURNED
        assert db_borrow.start_date.isoformat() == xmlevent.checked_out
        assert db_borrow.end_date.isoformat() == xmlevent.returned
        # currently returned unsaved
        assert not db_borrow.pk
        # notes should be copied
        assert db_borrow.notes == xmlevent.notes
        # should be associated with existing item
        assert db_borrow.item == poets

        # if author is in xml, should be added to item notes
        xmlevent.item.author = 'Knud Merrild'
        db_borrow = xmlevent.to_db_event(account)
        # get a fresh copy of the item to check
        poets = Item.objects.get(pk=poets.pk)
        assert 'Author: %s' % xmlevent.item.author in poets.notes

        # partial date, item with author
        Item.objects.create(mep_id='mep:000j03',
            title="Toussaint Louverture")
        xmlevent = xmlmap.load_xmlobject_from_string(self.partial_date,
            BorrowingEvent)
        db_borrow = xmlevent.to_db_event(account)
        assert db_borrow.start_date.year == 1956
        assert db_borrow.start_date.month == 1
        # no notes
        assert not db_borrow.notes

        xmlevent = xmlmap.load_xmlobject_from_string(self.bought, BorrowingEvent)
        db_borrow = xmlevent.to_db_event(account)
        assert db_borrow.item_status == Borrow.ITEM_BOUGHT
        # note should be copied from xml to database
        assert db_borrow.notes == xmlevent.notes
        # no item found - stub should automatically be created
        assert db_borrow.item
        assert db_borrow.item.title == xmlevent.item.title
        # simulate returned note
        xmlevent.notes = 'back'
        db_borrow = xmlevent.to_db_event(account)
        assert db_borrow.item_status == Borrow.ITEM_RETURNED

        # 1900 dates -> year unknown
        xmlevent = xmlmap.load_xmlobject_from_string(self.two_painters,
            BorrowingEvent)
        xmlevent.checked_out = datetime.date(1900, 5, 1)
        xmlevent.returned = datetime.date(1900, 6, 3)
        db_borrow = xmlevent.to_db_event(account)
        # check DatePrecision flags
        assert not db_borrow.start_date_precision.year
        assert db_borrow.start_date_precision.month
        assert db_borrow.start_date_precision.day
        assert not db_borrow.end_date_precision.year
        assert db_borrow.end_date_precision.month
        assert db_borrow.end_date_precision.day

        # deleted text should be added to notes
        xmlevent = xmlmap.load_xmlobject_from_string(self.del_text,
            BorrowingEvent)
        db_borrow = xmlevent.to_db_event(account)
        assert db_borrow.notes.startswith(xmlevent.notes)
        assert '<del' in db_borrow.notes
        assert '<bibl corresp="mep:000r7x">Wast</bibl>' in db_borrow.notes

        # extra dates should be added to notes
        xmlevent = xmlmap.load_xmlobject_from_string(self.extra_dates,
            BorrowingEvent)
        db_borrow = xmlevent.to_db_event(account)
        # serialize preserves namespace
        assert '<date when="1938-02-11">Feb 11 1938</date>' in db_borrow.notes
        assert '<date when="1938-02-11">Feb 11 1938</date>' in db_borrow.notes
        assert '<date when="1938-12-27">Dec 27</date>' in db_borrow.notes

        # bibliographic data added to notes
        xmlevent = xmlmap.load_xmlobject_from_string(self.bibl_pub_date,
            BorrowingEvent)
        db_borrow = xmlevent.to_db_event(account)
        assert 'Author: %s' % xmlevent.item.author in db_borrow.item.notes
        assert 'Publisher: %s' % xmlevent.item.publisher in db_borrow.item.notes
        assert 'Date: %s' % xmlevent.item.date in db_borrow.item.notes

        # biblscope data added to borrowing event notes (not item)
        xmlevent = xmlmap.load_xmlobject_from_string(self.biblscope,
            BorrowingEvent)
        db_borrow = xmlevent.to_db_event(account)
        assert 'number (Henry James No' in db_borrow.notes
        assert 'issue April - May 1934' in db_borrow.notes

        # item has no mep id
        xmlevent.item.mep_id = None
        db_borrow = xmlevent.to_db_event(account)
        assert isinstance(db_borrow.item, Item)
        assert str(db_borrow.item.title) == str(xmlevent.item.title)

       # include edition with bibl scope info
        xmlevent = xmlmap.load_xmlobject_from_string(self.edition,
            BorrowingEvent)
        db_borrow = xmlevent.to_db_event(account)
        assert db_borrow.notes.endswith('edition Everyman')

        # no title at all
        xmlevent = xmlmap.load_xmlobject_from_string(self.no_title,
            BorrowingEvent)
        db_borrow = xmlevent.to_db_event(account)
        assert isinstance(db_borrow.item, Item)
        assert db_borrow.item.title == '[no title]'


class TestLendingCard(TestCase):

    def test_fields(self):
        card = xmlmap.load_xmlobject_from_file(os.path.join(FIXTURE_DIR, 'sample-card.xml'),
            LendingCard)
        assert card.cardholders[0].name == 'Pauline Alderman'
        assert card.cardholders[0].mep_id == 'alde.pa'
        assert len(card.borrowing_events) == 18
        assert isinstance(card.borrowing_events[0], BorrowingEvent)
        assert card.image_base_path == 'pudl0123/825298/a/alderman/'
        assert len(card.surfaces) == 2
        assert isinstance(card.surfaces[0], FacsimileSurface)
        assert card.surfaces[0].xml_id == 's1'
        assert card.surfaces[0].url == '00000001.jp2'
        assert len(card.sides) == 2
        assert isinstance(card.sides[0], LendingCardSide)
        assert card.sides[0].facsimile_id == 's1'
        # in fixture, all borrows are on the first side
        assert len(card.sides[0].borrowing_events) == len(card.borrowing_events)
        assert isinstance(card.sides[0].borrowing_events[0], BorrowingEvent)
        assert card.sides[0].cardholders[0].mep_id == 'alde.pa'

    def test_surface_by_id(self):
        card = xmlmap.load_xmlobject_from_file(os.path.join(FIXTURE_DIR, 'sample-card.xml'),
            LendingCard)
        assert len(card.surface_by_id.keys()) == len(card.surfaces)
        assert card.surface_by_id['s1'] == card.surfaces[0].url
        assert card.surface_by_id['s2'] == card.surfaces[1].url

    def test_image_path(self):
        card = xmlmap.load_xmlobject_from_file(os.path.join(FIXTURE_DIR, 'sample-card.xml'),
            LendingCard)
        assert card.image_path('s1') == '%s%s' % (card.image_base_path,
            card.surfaces[0].url)


class TestBorrowedTitle(TestCase):

    def test_title_fields(self):
        item = xmlmap.load_xmlobject_from_string('''<row>
        <titleid>mep:00006j</titleid>
        <borrowerid>#alde.pa</borrowerid>
        <borrower_name>Pauline Alderman</borrower_name>
        <title>Midas' touch   </title>
        <regularized_title>Midas Touch</regularized_title>
    </row>''',
            BorrowedTitle)
        assert item.mep_id == 'mep:00006j'
        assert item.title == 'Midas Touch'
        assert item.unreg_title == "Midas' touch"

    def test_title_list(self):
        item_list = xmlmap.load_xmlobject_from_string('''<root>
            <row>
        <titleid>mep:00006j</titleid>
        <borrowerid>#alde.pa</borrowerid>
        <borrower_name>Pauline Alderman</borrower_name>
        <title>Midas' touch</title>
        <regularized_title>Midas Touch</regularized_title>
    </row>
    <row>
        <titleid>mep:00071x</titleid>
        <borrowerid>#bake</borrowerid>
        <borrower_name>Mrs. Thornton Baker</borrower_name>
        <title>Life of Oscar Wilde</title>
        <regularized_title>Life of Oscar Wilde</regularized_title>
    </row>
    </root>''',
            BorrowedTitles)
        assert len(item_list.titles) == 2
        assert isinstance(item_list.titles[0], BorrowedTitle)
