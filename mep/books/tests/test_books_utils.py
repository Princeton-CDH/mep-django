from django.test import TestCase

from mep.books.models import Work
from mep.books.utils import creator_lastname, nonstop_words, work_slug


def test_nonstop_words():
    assert nonstop_words('Time and Tide') == ['Time', 'Tide']
    assert nonstop_words('transition') == ['transition']
    assert nonstop_words('A Portrait of the Artist') == ['Portrait', 'Artist']
    assert nonstop_words("L'Infini Turbulent") == ['Infini', 'Turbulent']
    # TODO: test/improve can't/youth's


class TestCreatorLastname(TestCase):
    fixtures = ['multi_creator_work']

    def test_creator_lastname(self):
        # multi-author work fixture
        work = Work.objects.get(pk=4126)
        # use first author
        assert creator_lastname(work) == work.authors[0].short_name
        # if no author, use first editor
        work.creator_set.all().filter(creator_type__name='Author').delete()
        assert creator_lastname(work) == work.editors[0].short_name
        # if no authors or editors, no last name
        work.creator_set.all().delete()
        assert creator_lastname(work) == ''


class TestWorkSlug(TestCase):
    fixtures = ['multi_creator_work']

    def test_work_slug(self):
        # multi-author work fixture
        work = Work.objects.get(pk=4126)
        # title: The English Novelists: A Survey of the Novel ...
        assert work_slug(work) == 'bates-english-novelists-survey'
        assert work_slug(work, max_words=4) == \
            'bates-english-novelists-survey-novel'
