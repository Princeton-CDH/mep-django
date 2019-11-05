from unittest.mock import patch

from djiffy.models import Manifest
from parasolr.django.indexing import ModelIndexable
import pytest

from mep.accounts.models import Account
from mep.footnotes.models import Bibliography, BibliographySignalHandlers, \
    SourceType
from mep.people.models import Person


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_person_save(mock_indexitems):
    # unsaved - ignore
    pers = Person()
    BibliographySignalHandlers.person_save(Person, pers)
    mock_indexitems.assert_not_called()

    # saved but no account + card - ignore
    pers.save()
    BibliographySignalHandlers.person_save(Person, pers)
    mock_indexitems.assert_not_called()

    # associate an account; no card, still ignore
    acct = Account.objects.create()
    acct.persons.add(pers)
    BibliographySignalHandlers.person_save(Person, pers)
    mock_indexitems.assert_not_called()

    # associate card - should reindex
    src_type = SourceType.objects.create(name='website')
    acct.card = Bibliography.objects.create(source_type=src_type)
    acct.save()
    mock_indexitems.resetmock()
    BibliographySignalHandlers.person_save(Person, pers)
    # hits twice, once for person and once for bibliography (?!?)
    assert mock_indexitems.call_count == 2
    # person should be in the queryset; first arg for the last call
    assert acct.card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_person_delete(mock_indexitems):
    # unsaved - ignore
    pers = Person()
    BibliographySignalHandlers.person_delete(Person, pers)
    mock_indexitems.assert_not_called()

    # saved but no account + card - ignore
    pers.save()
    BibliographySignalHandlers.person_delete(Person, pers)
    mock_indexitems.assert_not_called()

    # associate an account; no card, still ignore
    acct = Account.objects.create()
    acct.persons.add(pers)
    BibliographySignalHandlers.person_delete(Person, pers)
    mock_indexitems.assert_not_called()

    # associate card - should reindex
    src_type = SourceType.objects.create(name='website')
    acct.card = Bibliography.objects.create(source_type=src_type)
    acct.save()
    mock_indexitems.resetmock()
    BibliographySignalHandlers.person_delete(Person, pers)
    # hits twice, once for person and once for bibliography (?!?)
    assert mock_indexitems.call_count == 2
    # person should be in the queryset; first arg for the last call
    assert acct.card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_account_save(mock_indexitems):
    # unsaved - ignore
    acct = Account()
    BibliographySignalHandlers.account_save(Account, acct)
    mock_indexitems.assert_not_called()

    # saved account; no card, still ignore
    acct.save()
    BibliographySignalHandlers.account_save(Account, acct)
    mock_indexitems.assert_not_called()

    # associate card - should reindex
    src_type = SourceType.objects.create(name='website')
    acct.card = Bibliography.objects.create(source_type=src_type)
    acct.save()
    mock_indexitems.resetmock()
    BibliographySignalHandlers.account_save(Account, acct)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert acct.card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_account_delete(mock_indexitems):
    # unsaved - ignore
    acct = Account()
    BibliographySignalHandlers.account_delete(Account, acct)
    mock_indexitems.assert_not_called()

    # saved account; no card, still ignore
    acct.save()
    BibliographySignalHandlers.account_delete(Account, acct)
    mock_indexitems.assert_not_called()

    # associate card - should reindex
    src_type = SourceType.objects.create(name='website')
    card = Bibliography.objects.create(source_type=src_type)
    acct.card = card
    acct.save()
    mock_indexitems.resetmock()
    BibliographySignalHandlers.account_delete(Account, acct)
    # hits twice, once for person and once for bibliography (?!?)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_manifest_save(mock_indexitems):
    # unsaved - ignore
    manif = Manifest()
    BibliographySignalHandlers.manifest_save(Manifest, manif)
    mock_indexitems.assert_not_called()

    # saved but no card; still ignore
    manif.save()
    BibliographySignalHandlers.manifest_save(Manifest, manif)
    mock_indexitems.assert_not_called()

    # associate card - should reindex
    src_type = SourceType.objects.create(name='website')
    card = Bibliography.objects.create(source_type=src_type,
                                       manifest=manif)
    mock_indexitems.resetmock()
    BibliographySignalHandlers.manifest_save(Manifest, manif)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_manifest_delete(mock_indexitems):
    # unsaved - ignore
    manif = Manifest()
    BibliographySignalHandlers.manifest_delete(Manifest, manif)
    mock_indexitems.assert_not_called()

    # saved but no card; still ignore
    manif.save()
    BibliographySignalHandlers.manifest_delete(Manifest, manif)
    mock_indexitems.assert_not_called()

    # associate card - should reindex
    src_type = SourceType.objects.create(name='website')
    card = Bibliography.objects.create(source_type=src_type,
                                       manifest=manif)
    BibliographySignalHandlers.manifest_delete(Manifest, manif)
    # hits twice, once for person and once for bibliography (?!?)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert card in mock_indexitems.call_args[0][0]
