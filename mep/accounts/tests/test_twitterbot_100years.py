from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from mep.accounts.management.commands import twitterbot_100years
from mep.books.models import Creator, CreatorType, Work
from mep.people.models import Person


class TestTwitterBot100years(TestCase):

    def setUp(self):
        self.cmd = twitterbot_100years.Command()
        self.cmd.stdout = StringIO()

    # def test_command_line(self):
    #     # test calling via command line with args
    #     stdout = StringIO()
    #     call_command('report_timegaps', csvtempfile.name, stdout=stdout)


class TestWorkLabel(TestCase):
    fixtures = ['sample_works']

    def test_authors(self):
        # - standard format: author's "title" (year), but handle multiple

        # no author, no year
        blue_train = Work.objects.get(pk=5)
        assert twitterbot_100years.work_label(blue_train) == \
            '“Murder on the Blue Train”'

        # single author with years
        exit_eliza = Work.objects.get(pk=1)
        assert twitterbot_100years.work_label(exit_eliza) == \
            "Barry Pain’s “Exit Eliza” (1912)"

        # add second author
        auth2 = Person.objects.create(name='Lara Cain', sort_name='Cain, Lara',
                                      slug='cain')
        author = CreatorType.objects.get(name='Author')
        Creator.objects.create(person=auth2, work=exit_eliza,
                               creator_type=author, order=2)
        assert twitterbot_100years.work_label(exit_eliza) == \
            "Barry Pain and Lara Cain’s “Exit Eliza” (1912)"

        # add third author
        auth3 = Person.objects.create(name='Mary Fain', sort_name='Fain, Mary',
                                      slug='fain')
        Creator.objects.create(person=auth3, work=exit_eliza,
                               creator_type=author, order=3)
        assert twitterbot_100years.work_label(exit_eliza) == \
            "Barry Pain et al.’s “Exit Eliza” (1912)"

    def test_editors(self):
        # editors listed if no author but editors

        # get work with no author
        blue_train = Work.objects.get(pk=5)

        # add editor
        ed1 = Person.objects.create(name='Lara Cain', sort_name='Cain, Lara',
                                    slug='cain')
        editor = CreatorType.objects.get(name='Editor')
        Creator.objects.create(person=ed1, work=blue_train,
                               creator_type=editor, order=1)
        assert twitterbot_100years.work_label(blue_train) == \
            "“Murder on the Blue Train,” edited by Lara Cain"
        # add second editor
        ed2 = Person.objects.create(name='Mara Vain', sort_name='Vain, Mara',
                                    slug='vain')
        Creator.objects.create(person=ed2, work=blue_train,
                               creator_type=editor, order=2)
        assert twitterbot_100years.work_label(blue_train) == \
            "“Murder on the Blue Train,” edited by Lara Cain and Mara Vain"
        # third editor
        ed3 = Person.objects.create(name='Nara Wain', sort_name='Wain, Nara',
                                    slug='wain')
        Creator.objects.create(person=ed3, work=blue_train,
                               creator_type=editor, order=3)
        assert twitterbot_100years.work_label(blue_train) == \
            "“Murder on the Blue Train,” edited by Lara Cain et al."

    def test_year(self):
        # set pre-modern publication date  — should not be included
        exit_eliza = Work.objects.get(pk=1)
        exit_eliza.year = 1350
        assert twitterbot_100years.work_label(exit_eliza) == \
            "Barry Pain’s “Exit Eliza”"

    def test_periodical(self):
        the_dial = Work.objects.get(pk=4598)
        assert twitterbot_100years.work_label(the_dial) == \
            "an issue of “The Dial”"
