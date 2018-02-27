import datetime
from unittest.mock import Mock

from django.test import TestCase
from django.template.defaultfilters import date as format_date

from mep.accounts.models import Account, Subscription, Borrow
from mep.people.forms import PersonChoiceField, PersonMergeForm
from mep.people.models import Person


class PersonChoiceFieldTest(TestCase):

    def test_label_from_instance(self):
        pchoicefield = PersonChoiceField(Mock())

        # should not error on record with minimal information
        pers = Person.objects.create(name='Jones')
        label = pchoicefield.label_from_instance(pers)
        assert pers.name in label

        # should display details if available
        pers = Person.objects.create(name='Jones', title='Mr',
            birth_year=1902, mep_id="jone", sex="M",
            viaf_id='http://viaf.org/viaf/1902010101',
            notes='more important details here')
        label = pchoicefield.label_from_instance(pers)
        assert '%s %s' % (pers.title, pers.name) in label
        assert '%s–\n' % pers.birth_year in label
        assert 'MEP id %s' % pers.mep_id in label
        assert '<a href="%(url)s" rel="nofollow">%(url)s</a>' % {'url': pers.viaf_id} \
            in label
        assert pers.notes in label

        # birth and death year when both are known
        pers.death_year = 1956
        label = pchoicefield.label_from_instance(pers)
        assert '%s–%s' % (pers.birth_year, pers.death_year) in label

        # display events if any
        acct = Account.objects.create()
        acct.persons.add(pers)
        subs = Subscription.objects.create(account=acct,
            start_date=datetime.datetime(1923, 1, 1), end_date=datetime.datetime(1924, 1, 1),
            notes='img204c')
        borrow = Borrow.objects.create(account=acct,
            start_date=datetime.datetime(1923, 5, 1), end_date=datetime.datetime(1923, 5, 15))
        label = pchoicefield.label_from_instance(pers)
        assert 'Subscription' in label
        # use template tag date format for consistency
        assert '%s–%s' % (format_date(subs.start_date), format_date(subs.end_date)) in label
        assert subs.notes in label
        assert 'Borrow' in label
        assert '%s–%s' % (format_date(borrow.start_date), format_date(borrow.end_date)) in label






