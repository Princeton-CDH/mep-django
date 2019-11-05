from unittest.mock import patch

from parasolr.django.indexing import ModelIndexable
from parasolr.django.signals import IndexableSignalHandler
import pytest

from mep.accounts.models import Account, Event
from mep.people.models import Country, Person, PersonSignalHandlers


def setup_module():
    # connect indexing signal handlers for this test module only
    IndexableSignalHandler.connect()


def teardown_module():
    # disconnect indexing signal handlers
    IndexableSignalHandler.disconnect()


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_country_save(mock_indexitems):
    uk = Country(
        name='United Kingdom', code='UK',
        geonames_id='http://sws.geonames.org/2635167/')

    # unsaved - ignore
    PersonSignalHandlers.country_save(Country, uk)
    mock_indexitems.assert_not_called()

    # saved but no members - ignore
    uk.save()
    PersonSignalHandlers.country_save(Country, uk)
    mock_indexitems.assert_not_called()

    # associate a person
    pers = Person.objects.create()
    # add nationality
    pers.nationalities.add(uk)
    # change country
    uk.name = 'Britannia'
    uk.save()
    PersonSignalHandlers.country_save(Country, uk)
    # person is not a library member - not called
    mock_indexitems.assert_not_called()

    # make person a library member
    acct = Account.objects.create()
    acct.persons.add(pers)
    PersonSignalHandlers.country_save(Country, uk)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert pers in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_country_delete(mock_indexitems):
    denmark = Country.objects.create(
        name='Denmark', code='DK',
        geonames_id='http://sws.geonames.org/2623032/')
    uk = Country.objects.create(
        name='United Kingdom', code='UK',
        geonames_id='http://sws.geonames.org/2635167/')

    # delete country with no members - nothing to do
    denmark.delete()
    PersonSignalHandlers.country_delete(Country, denmark)
    mock_indexitems.assert_not_called()

    # associate a person with an account
    pers = Person.objects.create()
    acct = Account.objects.create()
    acct.persons.add(pers)
    # add nationality
    pers.nationalities.add(uk)
    PersonSignalHandlers.country_delete(Country, uk)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert pers in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_account_save(mock_indexitems):
    # unsaved - ignore
    acct = Account()
    PersonSignalHandlers.account_save(Account, acct)
    mock_indexitems.assert_not_called()

    # saved but no people - ignore
    acct.save()
    PersonSignalHandlers.account_save(Account, acct)
    mock_indexitems.assert_not_called()

    # associate a person
    pers = Person.objects.create()
    acct.persons.add(pers)
    PersonSignalHandlers.account_save(Account, acct)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert pers in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_account_delete(mock_indexitems):
    acct = Account.objects.create()
    # saved but no people - ignore
    PersonSignalHandlers.account_delete(Account, acct)
    mock_indexitems.assert_not_called()

    # associate a person
    pers = Person.objects.create()
    acct.persons.add(pers)
    PersonSignalHandlers.account_delete(Account, acct)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert pers in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_event_save(mock_indexitems):
    # unsaved - ignore
    acct = Account.objects.create()
    evt = Event(account=acct)
    PersonSignalHandlers.event_save(Event, evt)
    mock_indexitems.assert_not_called()

    # saved but no people - ignore
    evt.save()
    PersonSignalHandlers.event_save(Event, evt)
    mock_indexitems.assert_not_called()

    # associate a person
    pers = Person.objects.create()
    acct.persons.add(pers)
    PersonSignalHandlers.event_save(Event, evt)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert pers in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_event_delete(mock_indexitems):
    acct = Account.objects.create()
    evt = Event.objects.create(account=acct)

    # saved but no people - ignore
    PersonSignalHandlers.event_delete(Event, evt)
    mock_indexitems.assert_not_called()

    # associate a person
    pers = Person.objects.create()
    acct.persons.add(pers)
    PersonSignalHandlers.event_delete(Event, evt)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert pers in mock_indexitems.call_args[0][0]
