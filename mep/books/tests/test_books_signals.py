from unittest.mock import patch

from parasolr.django.indexing import ModelIndexable
import pytest

from mep.books.models import Creator, CreatorType, Work, WorkSignalHandlers
from mep.people.models import Person


@pytest.mark.django_db
@patch.object(ModelIndexable, 'index_items')
def test_creatortype_save(mock_indexitems):
    new_type = CreatorType(name='Typesetter')
    # unsaved - ignored
    WorkSignalHandlers.creatortype_save(CreatorType, new_type)
    mock_indexitems.assert_not_called()

    author_type = CreatorType.objects.get(name='Author')
    # unsaved - ignore
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
    new_type = CreatorType.objects.create(name='Typesetter')
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
