from unittest.mock import Mock

from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse

from mep.accounts.models import Account
from mep.books.models import Creator, CreatorType, Item
from mep.people.admin import PersonAdmin, PersonTypeListFilter
from mep.people.models import Person


class TestPersonAdmin(TestCase):

    def test_merge_people(self):
        mockrequest = Mock()
        test_ids = ['5', '33', '101']
        # a dictionary mimes the request pattern of access
        mockrequest.session = {}
        mockrequest.POST.getlist.return_value = test_ids
        # code uses the built in methods of a dict, so making GET an
        # actual dict as it is for a request
        mockrequest.GET = {}
        resp = PersonAdmin(Person, Mock()).merge_people(mockrequest, Mock())
        assert isinstance(resp, HttpResponseRedirect)
        assert resp.status_code == 303
        assert resp['location'].startswith(reverse('people:merge'))
        assert resp['location'].endswith('?ids=%s' % ','.join(test_ids))
        # key should be set, but it should be an empty string
        assert 'people_merge_filter' in mockrequest.session
        assert not mockrequest.session['people_merge_filter']
        # Now add some values to be set as a query string on session
        mockrequest.GET = {'p': '3', 'filter': 'foo'}
        resp = PersonAdmin(Person, Mock()).merge_people(mockrequest, Mock())
        assert isinstance(resp, HttpResponseRedirect)
        assert resp.status_code == 303
        assert resp['location'].startswith(reverse('people:merge'))
        assert resp['location'].endswith('?ids=%s' % ','.join(test_ids))
        # key should be set and have a urlencoded string
        assert 'people_merge_filter' in mockrequest.session
        # test agnostic as to order since the querystring
        # works either way
        assert mockrequest.session['people_merge_filter'] in \
            ['p=3&filter=foo', 'filter=foo&p=3']

class TestPersonTypeListFilter(TestCase):
    
    def test_queryset(self):
        # create some test people
        humperdinck = Person(name='Humperdinck') # has an account
        engelbert = Person(name='Engelbert') # is a creator and has an account
        foo = Person(name='Foo') # uncategorized (not creator or member)
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
        # create a test item and creator
        item = Item(title='Le foo et le bar', year=1916, mep_id='lfelb')
        item.save()
        ctype = CreatorType(1)
        ctype.save()
        creator = Creator(creator_type=ctype, person=engelbert, item=item)
        creator.save()
        # sanity check our person types outside the admin
        assert humperdinck.has_account()
        assert engelbert.has_account()
        assert not foo.has_account()
        assert engelbert.is_creator()
        assert not humperdinck.is_creator()
        assert not foo.is_creator()
        # request only people with accounts (members)
        pfilter = PersonTypeListFilter(None, {'person_type': 'member'}, Person, PersonAdmin)
        qs = pfilter.queryset(None, Person.objects.all())
        assert humperdinck in qs
        assert engelbert in qs
        assert not foo in qs
        # request only people who are creators
        pfilter = PersonTypeListFilter(None, {'person_type': 'creator'}, Person, PersonAdmin)
        qs = pfilter.queryset(None, Person.objects.all())
        assert engelbert in qs
        assert not humperdinck in qs
        assert not foo in qs
        # request uncategorized people (neither members nor creators)
        pfilter = PersonTypeListFilter(None, {'person_type': 'uncategorized'}, Person, PersonAdmin)
        qs = pfilter.queryset(None, Person.objects.all())
        assert foo in qs
        assert not engelbert in qs
        assert not humperdinck in qs
