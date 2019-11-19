from unittest.mock import patch

from parasolr.django.indexing import ModelIndexable
import pytest

from mep.accounts.models import Account, Event, Address
from mep.people.models import Country, Person, Location, PersonSignalHandlers


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
    evt.save()
    PersonSignalHandlers.event_delete(Event, evt)
    mock_indexitems.assert_not_called()

    # associate a person
    pers = Person.objects.create()
    acct.persons.add(pers)
    PersonSignalHandlers.event_delete(Event, evt)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert pers in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_address_save(mock_indexitems):
    # none saved - ignore
    pers = Person.objects.create(name='Mr. Foo')
    loc = Location.objects.create(name='L\'Hotel', city='Paris')
    addr = Address(location=loc)
    PersonSignalHandlers.address_save(Address, addr)
    mock_indexitems.assert_not_called()

    # saved but associated directly to Person instead of their Account; ignore
    # NOTE this is a legacy pattern; included for completeness but shouldn't
    # occur in future as of 11/2019
    addr.person = pers
    addr.save()
    PersonSignalHandlers.address_save(Address, addr)
    mock_indexitems.assert_not_called()

    # associate an account with the address instead
    acct = Account.objects.create()
    acct.persons.add(pers)
    addr.person = None
    addr.account = acct
    addr.save()
    PersonSignalHandlers.address_save(Address, addr)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert pers in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_address_delete(mock_indexitems):
    pers = Person.objects.create(name='Mr. Foo')
    loc = Location.objects.create(name='L\'Hotel', city='Paris')
    addr = Address(location=loc)

    # associated directly to Person instead of their Account; ignore deletion
    # NOTE this is a legacy pattern; included for completeness but shouldn't
    # occur in future as of 11/2019
    addr.person = pers
    addr.save()
    PersonSignalHandlers.address_delete(Address, addr)
    mock_indexitems.assert_not_called()

    # associate an account with the address instead and delete it
    acct = Account.objects.create()
    acct.persons.add(pers)
    addr.person = None
    addr.account = acct
    addr.save()
    PersonSignalHandlers.address_delete(Address, addr)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert pers in mock_indexitems.call_args[0][0]