import datetime
from unittest.mock import Mock, patch

from django import forms
from django.test import TestCase
from django.template.defaultfilters import date as format_date

from mep.accounts.models import Account, Subscription, Borrow
from mep.books.models import Work
from mep.common.forms import ChoiceLabel, RadioSelectWithDisabled
from mep.people.forms import PersonChoiceField, PersonMergeForm, MemberSearchForm
from mep.people.models import Person


class PersonChoiceFieldTest(TestCase):
    def test_label_from_instance(self):
        pchoicefield = PersonChoiceField(Mock())

        # should not error on record with minimal information
        pers = Person.objects.create(name="Jones", slug="jones")
        label = pchoicefield.label_from_instance(pers)
        assert pers.name in label

        # should display details if available
        pers = Person.objects.create(
            name="Jones",
            title="Mr",
            slug="jones-2",
            birth_year=1902,
            mep_id="jone",
            gender="M",
            viaf_id="http://viaf.org/viaf/1902010101",
            notes="more important details here",
        )
        label = pchoicefield.label_from_instance(pers)
        assert "%s %s" % (pers.title, pers.name) in label
        assert "%s – \n" % pers.birth_year in label
        assert "MEP id %s" % pers.mep_id in label
        assert (
            '<a href="%(url)s" rel="nofollow">%(url)s</a>' % {"url": pers.viaf_id}
            in label
        )
        assert pers.notes in label

        # birth and death year when both are known
        pers.death_year = 1956
        label = pchoicefield.label_from_instance(pers)
        assert "%s – %s" % (pers.birth_year, pers.death_year) in label

        # display events if any
        acct = Account.objects.create()
        acct.persons.add(pers)
        subs = Subscription.objects.create(
            account=acct,
            start_date=datetime.datetime(1923, 1, 1),
            end_date=datetime.datetime(1924, 1, 1),
            notes="img204c",
        )
        work = Work.objects.create(title="Selected poem")
        borrow = Borrow.objects.create(
            account=acct,
            work=work,
            start_date=datetime.datetime(1923, 5, 1),
            end_date=datetime.datetime(1923, 5, 15),
        )
        label = pchoicefield.label_from_instance(pers)
        assert "Subscription" in label
        # use template tag date format for consistency
        assert (
            "%s – %s" % (format_date(subs.start_date), format_date(subs.end_date))
            in label
        )
        assert subs.notes in label
        assert "Borrow" in label
        assert (
            "%s – %s" % (format_date(borrow.start_date), format_date(borrow.end_date))
            in label
        )


class PersonMergeFormTest(TestCase):
    def test_init(self):
        # no error if person ids not specified
        PersonMergeForm()

        # create test person records
        Person.objects.bulk_create(
            [
                Person(name="Jones", slug="jones"),
                Person(name="Jones", title="Mr", slug="jones-2"),
                Person(name="Jones", title="Mr", gender="M", slug="jones-3"),
                Person(name="Jones", title="Mrs", slug="jones-4"),
            ]
        )
        # initialize with ids for all but the last
        peeps = Person.objects.all().order_by("pk")
        person_ids = list(peeps.values_list("id", flat=True))
        mergeform = PersonMergeForm(person_ids=person_ids[:-1])
        # total should have all but one person
        assert mergeform.fields["primary_person"].queryset.count() == peeps.count() - 1
        # last person should not be an available choice
        assert peeps.last() not in mergeform.fields["primary_person"].queryset


class TestRadioWithDisabled(TestCase):
    # test copied from ppa-django

    def setUp(self):
        class TestForm(forms.Form):
            """Build a test form use the widget"""

            CHOICES = (
                ("no", ChoiceLabel("no select", disabled=True)),
                ("yes", "yes can select"),
            )

            yes_no = forms.ChoiceField(choices=CHOICES, widget=RadioSelectWithDisabled)

        self.form = TestForm()

    def test_create_option(self):
        rendered = self.form.as_p()
        # no is disabled
        self.assertInHTML(
            '<input type="radio" name="yes_no" value="no" '
            'required id="id_yes_no_0" disabled="disabled" />',
            rendered,
        )
        # yes is not disabled
        self.assertInHTML(
            '<input type="radio" name="yes_no" value="yes" '
            'required id="id_yes_no_1" />',
            rendered,
        )


class TestMemberForm(TestCase):
    @patch("mep.people.forms.MemberSearchForm.set_range_minmax")
    def test_init(self, mock_range_minmax):
        data = {"has_card": True, "query": "Hemingway"}
        # has query, relevance enabled but sort disabled
        form = MemberSearchForm(data)
        assert form.fields["sort"].widget.choices[0] == form.SORT_CHOICES[0]
        assert form.fields["sort"].widget.choices[1][0] == "name"
        label = form.fields["sort"].widget.choices[1][1]
        assert isinstance(label, ChoiceLabel)
        assert label.label == "Name A – Z"
        assert label.disabled == True

        # empty query, relevance disabled
        data["query"] = ""
        form = MemberSearchForm(data)
        assert form.fields["sort"].widget.choices[0][0] == "relevance"
        label = form.fields["sort"].widget.choices[0][1]
        assert isinstance(label, ChoiceLabel)
        assert label.label == "Relevance"
        assert label.disabled == True

        # no query, also relevance disabled
        del data["query"]
        form = MemberSearchForm(data)
        assert form.fields["sort"].widget.choices[0][0] == "relevance"
        label = form.fields["sort"].widget.choices[0][1]
        assert isinstance(label, ChoiceLabel)
        assert label.label == "Relevance"
        assert label.disabled == True

        # should call set_range_placeholders with the value of range_minmax
        range_minmax = {"start_year": (1910, 1920)}
        form = MemberSearchForm(data, range_minmax=range_minmax)
        mock_range_minmax.assert_called_with(range_minmax)

    @patch("mep.common.forms.RangeField.set_min_max")
    def test_set_range_placeholders(self, mock_set_min_max):
        form = MemberSearchForm()

        range_minmax = {"birth_year": (1900, 1950), "membership_dates": (1918, 1951)}
        form.set_range_minmax(range_minmax)

        # Called twice on fields defined on the form using
        # min and max as integers
        mock_set_min_max.assert_any_call(1900, 1950)
        mock_set_min_max.assert_any_call(1918, 1951)
