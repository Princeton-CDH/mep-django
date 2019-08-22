import pytest

from mep.books.models import Work, Creator, CreatorType
from mep.books.migration_group_work_utils import ok_to_merge, similar_titles
from mep.people.models import Person


def test_similar_titles():

    # single title
    assert similar_titles(['Helene'])

    # exact same
    assert similar_titles(['Helene', 'Helene'])

    # variance in definite article
    assert similar_titles(['New Yorker', 'The New Yorker'])

    # variance in upper/lower case
    assert similar_titles(['New Yorker', 'a new yorker'])

    # slugify flattens accents
    assert similar_titles(['Françoise', 'Francoise'])

    # variation in initials
    assert similar_titles(['Short Stories of H.G. Wells',
                           'Short Stories of H. G. Wells'])

    # em dash and regular dash
    assert similar_titles(['Collected Poems, 1909–1935',
                           'Collected Poems, 1909-1935'])

    # not close enough
    assert not similar_titles(['Collected Poems, 1909–1935',
                               'Collected Poems'])


@pytest.mark.django_db
def test_ok_to_merge():

    # create two works with similar titles and no creators
    work1 = Work.objects.create(title='New Yorker')
    work2 = Work.objects.create(title='The New Yorker')
    works = Work.objects.all()

    assert ok_to_merge(works)

    # add an author to one
    author = CreatorType.objects.get(name='Author')
    person = Person.objects.create(name='John Foo')
    Creator.objects.create(person=person, creator_type=author, work=work1)

    assert not ok_to_merge(Work.objects.all())

    # match authors on works
    Creator.objects.create(person=person, creator_type=author, work=work2)
    assert ok_to_merge(Work.objects.all())

