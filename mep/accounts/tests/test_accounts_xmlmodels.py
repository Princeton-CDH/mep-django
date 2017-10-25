import datetime
import os
from mep.accounts.xml_models import LogBook, XmlEvent, Measure
from mep.accounts.models import Event, Subscribe, Reimbursement, FRF, Account
from mep.people.models import Person
from django.test import TestCase
from datetime import date

FIXTURE_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'fixtures'
)
XML_FIXTURE = os.path.join(FIXTURE_DIR, 'sample-logbook.xml')


class TestLogbook(TestCase):

    def test_from_file(self):
        logbook = LogBook.from_file(XML_FIXTURE)
        assert isinstance(logbook, LogBook)
        # Nine sample events included
        assert len(logbook.events) == 9


class TestEvent(TestCase):

    def setUp(self):
        self.logbook = LogBook.from_file(XML_FIXTURE)

    def test_attributes(self):
        monbrial = self.logbook.events[0]
        assert monbrial.e_type == 'subscription'
        assert monbrial.date == date(1921, 1, 5)
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

    def test_to_db_event(self):

        for event in self.logbook.events:
            event.to_db_event()
        # check that there are six events overall
        events = Event.objects.all()
        assert len(events) == 9

        # check that there are seven subscribes
        subscribes = Subscribe.objects.all()
        assert len(subscribes) == 7

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
        # there should be one in the fixture and its mep_id should be declos
        declos = Subscribe.objects.filter(sub_type=Subscribe.ADL)[0]
        assert declos
        assert declos.account.persons.first().mep_id == 'desc.au'

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

        # unknown e_type should raise a ValueError
        monbrial.e_type = 'foobar'
        with self.assertRaises(ValueError):
            monbrial._prepare_db_objects()

    def test__parse_subscribe(self):
        monbrial = self.logbook.events[0]

        # fake first step of _normalize to test normalize dates independently
        monbrial.common_dict = {
            'start_date': monbrial.date,
            'notes': '',
        }

        # - test with a standard subscribe
        monbrial._prepare_db_objects()
        monbrial._parse_subscribe()
        common_dict = monbrial.common_dict

        # should have set keys
        assert 'volumes' in common_dict
        assert 'price_paid' in common_dict
        assert 'deposit' in common_dict
        assert 'modification' not in common_dict

        # values pulled from XML correctly
        assert int(common_dict['volumes']) == 1
        assert int(common_dict['price_paid']) == 16
        assert float(common_dict['deposit']) == 7

        # - test handling for missing quantities, etc.
        monbrial.frequency.quantity = None
        monbrial._parse_subscribe()
        assert 'Subscribe missing data:\n' in monbrial.common_dict['notes']
        assert 'Volumes: None' in monbrial.common_dict['notes']
        assert 'Duration: 3' in monbrial.common_dict['notes']
        assert 'Price Paid: 16' in monbrial.common_dict['notes']
        # now the rest also need to be cleared to make sure note logic works
        monbrial.price.quantity = None
        monbrial.deposit.quantity = None
        monbrial.duration.quantity = None
        print(monbrial.common_dict)
        monbrial._parse_subscribe()
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

        a = ['A', 'A.', 'a']
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

    def test__normalize_dates(self):

        monbrial = self.logbook.events[0]
        # fake first step of _normalize to test normalize dates independently
        monbrial.common_dict = {
            'start_date': monbrial.date,
            'notes': '',
        }
        monbrial._normalize_dates()
        # should show a three month interval
        assert monbrial.common_dict['start_date'] == date(1921, 1, 5)
        assert monbrial.common_dict['end_date'] == date(1921, 4, 5)

        # make the duration quantity one
        monbrial.duration.quantity = 1
        monbrial._normalize_dates()
        assert monbrial.common_dict['end_date'] == date(1921, 2, 5)

        # - test float variation cases
        monbrial.duration.quantity = '.25'
        monbrial._normalize_dates()
        assert monbrial.common_dict['end_date'] == date(1921, 1, 12)

        monbrial.duration.quantity = '.5'
        monbrial._normalize_dates()
        assert monbrial.common_dict['end_date'] == date(1921, 1, 19)

        # - duration given in days
        monbrial.duration.quantity = '7'
        monbrial.duration.unit = 'day'
        monbrial._normalize_dates()
        assert monbrial.common_dict['end_date'] == date(1921, 1, 12)
