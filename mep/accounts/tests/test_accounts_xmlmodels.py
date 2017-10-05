import datetime
import os
from mep.accounts.xml_models import LogBook, XmlEvent
from mep.accounts.models import Event, Subscribe
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
        assert len(logbook.day_divs) == 3


class TestDayDiv(TestCase):

    def setUp(self):
        self.logbook = LogBook.from_file(XML_FIXTURE)

    def test_no_event(self):

        # First check no events (i.e. first entry in fixture has no events)
        empty_div = self.logbook.day_divs[0]
        assert len(empty_div.dates) == 1
        assert empty_div.dates[0].iso_date == '1921-01-01'

    def test_events(self):
        # Get a div that has events
        event_div = self.logbook.day_divs[1]
        assert event_div.events
        # First one should have three
        assert len(event_div.events) == 3
        # they should be instances of mep.accounts.xmlmodels.Event
        assert isinstance(event_div.events[0], XmlEvent)


class TestEvent(TestCase):

    def setUp(self):
        self.logbook = LogBook.from_file(XML_FIXTURE)

    def test_attributes(self):

        event_div = self.logbook.day_divs[1]

        monbrial = event_div.events[0]
        assert monbrial.e_type == 'subscription'
        assert monbrial.mepid == '#monb'
        assert monbrial.name == 'Mlle Monbrial'
        assert monbrial.duration_unit == 'month'
        assert monbrial.duration_quantity == '3'
        assert monbrial.frequency_unit == 'volume'
        assert monbrial.frequency_quantity == '1'
        assert monbrial.price_unit == 'franc'
        assert monbrial.price_quantity == '16'
        assert monbrial.deposit_unit == 'franc'
        assert monbrial.deposit_quantity == '7'

    def test_to_db_event(self):


        # - check subcribe type events to db model
        events = self.logbook.day_divs[1].events
        date = self.logbook.day_divs[1].dates[0]
        for event in events:
            event.to_db_event(date.iso_date)


        # check that there are three events overall
        events = Event.objects.all()
        assert len(events) == 3

        # check that there are three subscribes
        subscribes = Subscribe.objects.all()
        assert len(subscribes) == 3

        # check one in detail
        monbrial = subscribes.filter(account__persons__mep_id='monb')[0]
        assert monbrial.start_date == datetime.date(1921, 1, 5)
        assert monbrial.end_date == datetime.date(1921, 1, 5)
        assert monbrial.duration == 3
        assert monbrial.currency == 'FRF'
        assert monbrial.deposit == 7
        assert monbrial.price_paid == 16
