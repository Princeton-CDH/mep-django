import datetime
import os
from mep.accounts.xml_models import LogBook, XmlEvent
from mep.accounts.models import Event, Subscribe, Reimbursement, FRF, Account
from mep.people.models import Person
from django.test import TestCase


FIXTURE_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'fixtures'
)
XML_FIXTURE = os.path.join(FIXTURE_DIR, 'sample-logbook.xml')


class TestLogbook(TestCase):

    def test_from_file(self):
        logbook = LogBook.from_file(XML_FIXTURE)
        assert isinstance(logbook, LogBook)
        # Three day divs included
        assert len(logbook.days) == 3


class TestDayDiv(TestCase):

    def setUp(self):
        self.logbook = LogBook.from_file(XML_FIXTURE)

    def test_no_event(self):

        # First check no events (i.e. first entry in fixture has no events)
        empty_day = self.logbook.days[0]
        assert empty_day.date == datetime.date(1921, 1, 1)
        assert not empty_day.events

    def test_events(self):
        # Get a div that has events
        day = self.logbook.days[2]
        assert day.events
        # First one should have three
        assert len(day.events) == 3
        # they should be instances of mep.accounts.xmlmodels.Event
        assert isinstance(day.events[0], XmlEvent)


class TestEvent(TestCase):

    def setUp(self):
        self.logbook = LogBook.from_file(XML_FIXTURE)

    def test_attributes(self):

        day = self.logbook.days[1]

        monbrial = day.events[0]
        assert monbrial.e_type == 'subscription'
        assert monbrial.mepid == '#monb'
        assert monbrial.name == 'Mlle Monbrial'
        assert monbrial.duration_unit == 'month'
        assert monbrial.duration_quantity == '3'
        assert monbrial.frequency_unit == 'volume'
        assert monbrial.frequency_quantity == 1
        assert monbrial.price_unit == 'franc'
        assert monbrial.price_quantity == '16'
        assert monbrial.deposit_unit == 'franc'
        assert monbrial.deposit_quantity == '7'
        assert not monbrial.sub_type

    def test_to_db_event(self):

        # - check subcribe type events to db model
        events = self.logbook.days[1].events
        date = self.logbook.days[1].date
        for event in events:
            event.to_db_event(date)
        # check that there are six events overall
        events = Event.objects.all()
        assert len(events) == 6

        # check that there are four subscribes
        subscribes = Subscribe.objects.all()
        assert len(subscribes) == 4

        # check one in detail
        monbrial = subscribes.filter(account__persons__mep_id='monb')[0]
        assert monbrial.start_date == datetime.date(1921, 1, 5)
        assert monbrial.end_date == datetime.date(1921, 4, 5)
        assert monbrial.duration == 3
        assert monbrial.currency == FRF
        assert monbrial.deposit == 7
        assert monbrial.price_paid == 16

        # check the reimbursement because it's different enough
        kunst = Reimbursement.objects.get(account__persons__mep_id__icontains='kunst')
        assert kunst.start_date == datetime.date(1921, 1, 5)
        # no duration, no end date
        assert not kunst.end_date
        assert kunst.currency == FRF
        assert kunst.price == 200

        # check reimbursements that use <measure type="reimbursement" ... >
        burning = Reimbursement.objects.get(account__persons__mep_id__icontains='burning')
        assert burning.currency == FRF
        assert burning.price == 50

        # check a subscription that should have a subclass
        # - is in day[2]
        # - check subcribe type events to db model
        events = self.logbook.days[2].events
        date = self.logbook.days[2].date
        for event in events:
            event.to_db_event(date)
        # - there should be one in the fixture and its mep_id should be declos
        declos = Subscribe.objects.filter(sub_type=Subscribe.ADL)[0]
        assert declos
        assert declos.account.persons.first().mep_id == 'desc.au'

    def test__is_int(self):
        day = self.logbook.days[1]
        event = day.events[0]
        assert event._is_int("7")
        assert not event._is_int("foobar")

    def test__normalize(self):
        day = self.logbook.days[1]
        monbrial = day.events[0]

        # - test basic functionality on a standard subscribe
        etype, person, account = monbrial._normalize(day.date)

        # should have set type for django database
        assert etype == 'subscribe'
        assert monbrial.common_dict == {
            'currency': FRF,
            'notes': '',
            'duration': 3,
            'start_date': datetime.date(1921, 1, 5),
            'end_date': datetime.date(1921, 4, 5),
        }

        # should have created a person stub and an associated account
        assert person == Person.objects.get(mep_id='monb')
        assert account == Account.objects.get(persons__in=[person])

    def test__parse_subscribe(self):
        day = self.logbook.days[1]
        monbrial = day.events[0]

        # - test with a standard subscribe
        etype, person, account = monbrial._normalize(day.date)
        monbrial._parse_subscribe()
        common_dict = monbrial.common_dict

        # should have set keys
        assert 'volumes' in common_dict
        assert 'price_paid' in common_dict
        assert 'deposit' in common_dict
        assert 'modification' not in common_dict

        # values pulled from XML correctly
        assert common_dict['volumes'] == 1
        assert int(common_dict['price_paid']) == 16
        assert float(common_dict['deposit']) == 7

    def test__set_subtype(self):
        # - basic event, no subtype
        day = self.logbook.days[1]
        monbrial = day.events[0]
        monbrial._normalize(day.date)
        monbrial._set_subtype()
        assert 'sub_type' not in monbrial.common_dict
        # - add sub_type
        monbrial.sub_type = 'A.d.c'
        monbrial._set_subtype()
        assert monbrial.common_dict['sub_type'] == Subscribe.OTHER

        # - test sub_types comprehensively using variations from the MEP report
        stu = ['(stud.)', 'Student', '(Stud)', 'st', 'St.', '/ Stud/']
        for var in stu:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['sub_type'] == Subscribe.STU

        prof = ['Professor', 'Prof', 'Pr', '(Prof.)']
        for var in prof:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['sub_type'] == Subscribe.PROF

        a =  ['A', 'A.', 'a']
        for var in a:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['sub_type'] == Subscribe.A

        b = ['B', 'B.', 'b']
        for var in b:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['sub_type'] == Subscribe.B

        ab = ['B+A', 'A + B', 'B + A', 'a and b', 'A and B']
        for var in ab:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['sub_type'] == Subscribe.A_B

        adl = ['A.des.l', 'ADL', 'A. d. L.', 'AdL']
        for var in adl:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['sub_type'] == Subscribe.ADL

        other = ['D.D.', 'A.S.L', 'foo', 'bar']
        for var in other:
            monbrial.sub_type = var
            monbrial._set_subtype()
            assert monbrial.common_dict['sub_type'] == Subscribe.OTHER