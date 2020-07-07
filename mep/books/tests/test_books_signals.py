from unittest.mock import patch

import pytest
from parasolr.django.indexing import ModelIndexable

from mep.accounts.models import Account, Event
from mep.books.models import (Creator, CreatorType, Format, Work,
                              WorkSignalHandlers)
from mep.people.models import Person


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_creatortype_save(mock_indexitems):
    new_type = CreatorType(name='Typesetter')
    # unsaved - ignored
    WorkSignalHandlers.creatortype_save(CreatorType, new_type)
    mock_indexitems.assert_not_called()

    author_type = CreatorType.objects.get(name='Author')
    # saved but no associated books
    WorkSignalHandlers.creatortype_save(CreatorType, author_type)
    mock_indexitems.assert_not_called()

    # associate a work
    work = Work.objects.create(title='Poems', year=1916)
    author1 = Person.objects.create(name='Smith')
    # add one each of author, editor, and translator
    Creator.objects.create(
        creator_type=author_type, person=author1, work=work)
    WorkSignalHandlers.creatortype_save(CreatorType, author_type)
    assert mock_indexitems.call_count == 1
    assert work in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_creatortype_delete(mock_indexitems):
    # no associated works - ignored
    new_type = CreatorType.objects.create(name='Typesetter', order=6)
    WorkSignalHandlers.creatortype_delete(CreatorType, new_type)
    mock_indexitems.assert_not_called()

    author_type = CreatorType.objects.get(name='Author')
    # associate a work
    work = Work.objects.create(title='Poems', year=1916)
    author1 = Person.objects.create(name='Smith')
    # add one each of author, editor, and translator
    Creator.objects.create(
        creator_type=author_type, person=author1, work=work)
    WorkSignalHandlers.creatortype_delete(CreatorType, author_type)
    assert mock_indexitems.call_count == 1
    assert work in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_person_save(mock_indexitems):
    # unsaved - ignore
    pers = Person()
    WorkSignalHandlers.person_save(Person, pers)
    mock_indexitems.assert_not_called()

    # saved but no works - ignore
    pers.save()
    WorkSignalHandlers.person_save(Person, pers)
    mock_indexitems.assert_not_called()

    # associate a work
    author_type = CreatorType.objects.get(name='Author')
    # associate a work
    work = Work.objects.create(title='Poems', year=1916)
    # add one each of author, editor, and translator
    Creator.objects.create(
        creator_type=author_type, person=pers, work=work)
    WorkSignalHandlers.person_save(Person, pers)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert work in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_person_delete(mock_indexitems):
    # saved but no works - ignore
    pers = Person.objects.create()
    WorkSignalHandlers.person_delete(Person, pers)
    mock_indexitems.assert_not_called()

    # associate a work
    author_type = CreatorType.objects.get(name='Author')
    # associate a work
    work = Work.objects.create(title='Poems', year=1916)
    # add one each of author, editor, and translator
    Creator.objects.create(
        creator_type=author_type, person=pers, work=work)
    WorkSignalHandlers.person_delete(Person, pers)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert work in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_creator_change(mock_indexitems):
    # create person, work, and creator
    pers = Person.objects.create()
    author_type = CreatorType.objects.get(name='Author')
    work = Work.objects.create(title='Poems', year=1916)

    # unsaved - ignore
    creator = Creator(creator_type=author_type, person=pers, work=work)

    WorkSignalHandlers.creator_change(Creator, creator)
    mock_indexitems.assert_not_called()

    # saved
    creator.save()
    WorkSignalHandlers.creator_change(Creator, creator)
    assert mock_indexitems.call_count == 1
    # person should be in the queryset; first arg for the last call
    assert mock_indexitems.called_with([work])


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_format_save(mock_indexitems):
    # not associated with work; ignore
    zine = Format.objects.create(name="zine")
    WorkSignalHandlers.format_save(Format, zine)
    mock_indexitems.assert_not_called()

    # associate with work; should be called
    poems = Work.objects.create(title='Poems', year=1916, work_format=zine)
    WorkSignalHandlers.format_save(Format, zine)
    assert mock_indexitems.call_count == 1
    assert poems in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_format_delete(mock_indexitems):
    # not associated with work; ignore
    zine = Format.objects.create(name="zine")
    WorkSignalHandlers.format_delete(Format, zine)
    mock_indexitems.assert_not_called()

    # associate with work; should be called
    poems = Work.objects.create(title='Poems', year=1916, work_format=zine)
    WorkSignalHandlers.format_delete(Format, zine)
    assert mock_indexitems.call_count == 1
    assert poems in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_event_save(mock_indexitems):
    # not associated with work; ignore
    acct = Account.objects.create()
    ev = Event.objects.create(account=acct)
    WorkSignalHandlers.event_save(Event, ev)
    mock_indexitems.assert_not_called()

    # associate with work; should be called
    poems = Work.objects.create(title='Poems', year=1916)
    ev.work = poems
    WorkSignalHandlers.event_save(Event, ev)
    assert mock_indexitems.call_count == 1
    assert poems in mock_indexitems.call_args[0][0]


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_event_delete(mock_indexitems):
    # not associated with work; ignore
    acct = Account.objects.create()
    ev = Event.objects.create(account=acct)
    WorkSignalHandlers.event_delete(Event, ev)
    mock_indexitems.assert_not_called()

    # associate with work; should be called
    poems = Work.objects.create(title='Poems', year=1916)
    ev.work = poems
    WorkSignalHandlers.event_delete(Event, ev)
