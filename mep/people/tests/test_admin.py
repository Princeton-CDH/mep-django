from unittest.mock import Mock, patch

from django.contrib import admin
from datetime import date

from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from mep.accounts.models import Account, Subscription
from mep.books.models import Creator, CreatorType, Work
from mep.people.admin import PersonAdmin, PersonTypeListFilter
from mep.people.models import Person, PastPersonSlug


class TestPersonAdmin(TestCase):
    fixtures = ["sample_people"]

    def test_merge_people(self):
        mockrequest = Mock()
        test_ids = ["5", "33", "101"]
        # a dictionary mimes the request pattern of access
        mockrequest.session = {}
        mockrequest.POST.getlist.return_value = test_ids
        # code uses the built in methods of a dict, so making GET an
        # actual dict as it is for a request
        mockrequest.GET = {}
        resp = PersonAdmin(Person, Mock()).merge_people(mockrequest, Mock())
        assert isinstance(resp, HttpResponseRedirect)
        assert resp.status_code == 303
        assert resp["location"].startswith(reverse("people:merge"))
        assert resp["location"].endswith("?ids=%s" % ",".join(test_ids))
        # key should be set, but it should be an empty string
        assert "people_merge_filter" in mockrequest.session
        assert not mockrequest.session["people_merge_filter"]
        # Now add some values to be set as a query string on session
        mockrequest.GET = {"p": "3", "filter": "foo"}
        resp = PersonAdmin(Person, Mock()).merge_people(mockrequest, Mock())
        assert isinstance(resp, HttpResponseRedirect)
        assert resp.status_code == 303
        assert resp["location"].startswith(reverse("people:merge"))
        assert resp["location"].endswith("?ids=%s" % ",".join(test_ids))
        # key should be set and have a urlencoded string
        assert "people_merge_filter" in mockrequest.session
        # test agnostic as to order since the querystring
        # works either way
        assert mockrequest.session["people_merge_filter"] in [
            "p=3&filter=foo",
            "filter=foo&p=3",
        ]

    def test_tabulate_queryset(self):
        person_admin = PersonAdmin(model=Person, admin_site=admin.site)
        people = Person.objects.order_by("id").all()
        # create at least one subscription so that the subscription_list
        # test is meaningful
        account = people[0].account_set.first()
        Subscription.objects.create(
            start_date=date(1955, 1, 6), end_date=date(1955, 1, 8), account=account
        )
        # test that tabular data matches queryset data
        for person, person_data in zip(people, person_admin.tabulate_queryset(people)):
            # test some properties
            assert person.name in person_data
            assert person.mep_id in person_data
            assert person.updated_at in person_data
            # test some methods
            assert person.is_creator() in person_data
            assert person.has_account() in person_data
            assert person.admin_url() in person_data
            assert person.subscription_dates() in person_data

    @patch("mep.people.admin.export_to_csv_response")
    def test_export_csv(self, mock_export_to_csv_response):
        person_admin = PersonAdmin(model=Person, admin_site=admin.site)
        with patch.object(person_admin, "tabulate_queryset") as tabulate_queryset:
            # if no queryset provided, should use default queryset
            people = person_admin.get_queryset(Mock())
            person_admin.export_to_csv(Mock())
            assert tabulate_queryset.called_once_with(people)
            # otherwise should respect the provided queryset
            first_person = Person.objects.all()[:0]
            person_admin.export_to_csv(Mock(), first_person)
            assert tabulate_queryset.called_once_with(first_person)

            export_args, export_kwargs = mock_export_to_csv_response.call_args
            # first arg is filename
            csvfilename = export_args[0]
            assert csvfilename.endswith(".csv")
            assert csvfilename.startswith("mep-people")
            # should include current date
            assert now().strftime("%Y%m%d") in csvfilename
            headers = export_args[1]
            # should use verbose name from db model field
            assert "MEP id" in headers
            # or verbose name for property
            assert "Admin Link" in headers
            # or title case for property with no verbose name
            assert "Is Creator" in headers

    def test_past_slugs_list(self):
        person_admin = PersonAdmin(model=Person, admin_site=admin.site)
        person = Person.objects.order_by("id").first()
        # no object = no error but no value
        assert not person_admin.past_slugs_list()
        # empty string for person with no past slugs
        assert person_admin.past_slugs_list(person) == ""
        # add slugs
        old_slugs = ["old-slug1", "old-slug2", "snail"]
        for slug in old_slugs:
            PastPersonSlug.objects.create(person=person, slug=slug)
        assert person_admin.past_slugs_list(person) == ", ".join(old_slugs)


class TestPersonTypeListFilter(TestCase):
    def test_queryset(self):
        # create some test people
        # - has an account
        humperdinck = Person(name="Humperdinck", slug="humperdinck")
        # - is a creator and has an account
        engelbert = Person(name="Engelbert", slug="engelbert")
        # uncategorized (not creator or member)
        foo = Person(name="Foo", slug="foo")
        humperdinck.save()
        engelbert.save()
        foo.save()
        # create some test accounts for the people
        h_acc = Account.objects.create()
        h_acc.persons.add(humperdinck)
        h_acc.save()
        e_acc = Account.objects.create()
        e_acc.persons.add(engelbert)
        e_acc.save()
        # create a test work and creator
        work = Work(title="Le foo et le bar", year=1916, mep_id="lfelb")
        work.save()
        ctype = CreatorType(1, order=1)
        ctype.save()
        creator = Creator(creator_type=ctype, person=engelbert, work=work)
        creator.save()
        # sanity check our person types outside the admin
        assert humperdinck.has_account()
        assert engelbert.has_account()
        assert not foo.has_account()
        assert engelbert.is_creator()
        assert not humperdinck.is_creator()
        assert not foo.is_creator()
        # request only people with accounts (members)
        pfilter = PersonTypeListFilter(
            None, {"person_type": "member"}, Person, PersonAdmin
        )
        qs = pfilter.queryset(None, Person.objects.all())
        assert humperdinck in qs
        assert engelbert in qs
        assert not foo in qs
        # request only people who are creators
        pfilter = PersonTypeListFilter(
            None, {"person_type": "creator"}, Person, PersonAdmin
        )
        qs = pfilter.queryset(None, Person.objects.all())
        assert engelbert in qs
        assert not humperdinck in qs
        assert not foo in qs
        # request uncategorized people (neither members nor creators)
        pfilter = PersonTypeListFilter(
            None, {"person_type": "uncategorized"}, Person, PersonAdmin
        )
        qs = pfilter.queryset(None, Person.objects.all())
        assert foo in qs
        assert not engelbert in qs
        assert not humperdinck in qs
