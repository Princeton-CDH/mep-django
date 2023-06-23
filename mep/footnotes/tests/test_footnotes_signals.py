from unittest.mock import patch

from djiffy.models import Canvas, Manifest
from parasolr.django.indexing import ModelIndexable
import pytest

from mep.accounts.models import Account, Event
from mep.footnotes.models import Bibliography, BibliographySignalHandlers, SourceType
from mep.people.models import Person


@pytest.mark.django_db
@patch.object(ModelIndexable, "index_items")
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
    src_type = SourceType.objects.create(name="website")
    acct.card = Bibliography.objects.create(source_type=src_type)
    acct.save()
    mock_indexitems.resetmock()
    BibliographySignalHandlers.person_save(Person, pers)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert acct.card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, "index_items")
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
    src_type = SourceType.objects.create(name="website")
    acct.card = Bibliography.objects.create(source_type=src_type)
    acct.save()
    mock_indexitems.resetmock()
    BibliographySignalHandlers.person_delete(Person, pers)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert acct.card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, "index_items")
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
    src_type = SourceType.objects.create(name="website")
    acct.card = Bibliography.objects.create(source_type=src_type)
    acct.save()
    mock_indexitems.resetmock()
    BibliographySignalHandlers.account_save(Account, acct)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert acct.card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, "index_items")
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
    src_type = SourceType.objects.create(name="website")
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
@patch.object(ModelIndexable, "index_items")
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
    src_type = SourceType.objects.create(name="website")
    card = Bibliography.objects.create(source_type=src_type, manifest=manif)
    mock_indexitems.resetmock()
    BibliographySignalHandlers.manifest_save(Manifest, manif)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, "index_items")
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
    src_type = SourceType.objects.create(name="website")
    card = Bibliography.objects.create(source_type=src_type, manifest=manif)
    BibliographySignalHandlers.manifest_delete(Manifest, manif)
    # hits twice, once for person and once for bibliography (?!?)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, "index_items")
def test_canvas_save(mock_indexitems):
    # unsaved - ignore
    manif = Manifest.objects.create()
    page = Canvas(manifest=manif, order=1)
    BibliographySignalHandlers.canvas_save(Canvas, page)
    mock_indexitems.assert_not_called()

    # saved but no card; still ignore
    page.save()
    BibliographySignalHandlers.canvas_save(Canvas, page)
    mock_indexitems.assert_not_called()

    # associate card - should reindex
    src_type = SourceType.objects.create(name="website")
    card = Bibliography.objects.create(source_type=src_type, manifest=manif)
    mock_indexitems.resetmock()
    BibliographySignalHandlers.canvas_save(Canvas, page)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, "index_items")
def test_canvas_delete(mock_indexitems):
    # unsaved - ignore
    manif = Manifest()
    page = Canvas(manifest=manif, order=1)
    BibliographySignalHandlers.canvas_delete(Canvas, page)
    mock_indexitems.assert_not_called()

    # saved but no card; still ignore
    manif.save()
    BibliographySignalHandlers.canvas_delete(Canvas, page)
    mock_indexitems.assert_not_called()

    # associate card - should reindex
    src_type = SourceType.objects.create(name="website")
    card = Bibliography.objects.create(source_type=src_type, manifest=manif)
    BibliographySignalHandlers.canvas_delete(Canvas, page)
    # hits twice, once for person and once for bibliography (?!?)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, "index_items")
def test_event_save(mock_indexitems):
    # unsaved - ignore
    acct = Account.objects.create()
    evt = Event(account=acct)
    BibliographySignalHandlers.event_save(Event, evt)
    mock_indexitems.assert_not_called()

    # saved account; no card, still ignore
    evt.save()
    BibliographySignalHandlers.event_save(Event, evt)
    mock_indexitems.assert_not_called()

    # associate card - should reindex
    src_type = SourceType.objects.create(name="website")
    acct.card = Bibliography.objects.create(source_type=src_type)
    acct.save()
    mock_indexitems.resetmock()
    BibliographySignalHandlers.event_save(Event, evt)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert acct.card in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, "index_items")
def test_event_delete(mock_indexitems):
    # unsaved - ignore
    acct = Account.objects.create()
    evt = Event(account=acct)
    BibliographySignalHandlers.event_delete(Event, evt)
    mock_indexitems.assert_not_called()

    # saved account; no card, still ignore
    evt.save()
    BibliographySignalHandlers.event_delete(Event, evt)
    mock_indexitems.assert_not_called()

    # associate card - should reindex
    src_type = SourceType.objects.create(name="website")
    card = Bibliography.objects.create(source_type=src_type)
    acct.card = card
    acct.save()
    mock_indexitems.resetmock()
    BibliographySignalHandlers.event_delete(Event, evt)
    # hits twice, once for person and once for bibliography (?!?)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert card in mock_indexitems.call_args[0][0]
