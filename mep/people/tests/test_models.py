import datetime
import re
from datetime import date
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned, ValidationError
from django.test import TestCase
from django.urls import resolve
from django.utils import timezone
from viapy.api import ViafEntity

from mep.accounts.models import Account, Address, Reimbursement, Subscription
from mep.books.models import Creator, CreatorType, Work
from mep.footnotes.models import Bibliography, Footnote, SourceType
from mep.people.models import (Country, InfoURL, Location, Person, Profession,
                               Relationship, RelationshipType)


class TestLocation(TestCase):

    def test_repr(self):
        loc = Location(name='L\'Hotel', city='Paris')
        # unsaved
        assert repr(loc) == '<Location pk:?? %s>' % str(loc)
        # saved
        loc.save()
        assert repr(loc) == '<Location pk:%s %s>' % (loc.pk, str(loc))

    def test_str(self):
        hotel = Location.objects.create(name='L\'Hotel')
        assert str(hotel) == hotel.name
        paris_hotel = Location.objects.create(name='L\'Hotel', city='Paris')
        assert str(paris_hotel) == '%s, %s' % (paris_hotel.name, paris_hotel.city)


class TestPerson(TestCase):

    def test_str(self):
        # Use name if sort name is not set
        person_foo = Person(name='Foo')
        assert str(person_foo) == 'Foo'

        # Use sort name if available
        foo_bar = Person(name='Foo Bar', sort_name='Bar, Foo')
        assert str(foo_bar) == 'Bar, Foo'

        # Add title if it exists
        foo_bar = Person(name='Bar', title='Mr.')
        assert str(foo_bar) == 'Mr. Bar'

        # if last, first, title goes after
        foo_bar = Person(sort_name='Bar, Foo', title='Mr.')
        assert str(foo_bar) == 'Bar, Foo, Mr.'

        # if not last first, in front
        foo_bar = Person(sort_name='Bar', title='Mr.')
        assert str(foo_bar) == 'Mr. Bar'

    def test_repr(self):
        person_foo = Person(name='Foo', sort_name='Bar, Foo')
        # unsaved
        assert repr(person_foo) == '<Person pk:?? %s>' % person_foo.sort_name
        # saved
        person_foo.save()
        assert repr(person_foo) == '<Person pk:%s %s>' % \
            (person_foo.pk, person_foo.sort_name)

    def test_viaf(self):
        pers = Person(name='Beach')
        assert pers.viaf is None
        pers.viaf_id = 'http://viaf.org/viaf/35247539'
        assert isinstance(pers.viaf, ViafEntity)
        assert pers.viaf.uri == pers.viaf_id

    def test_short_name(self):
        # should return up to comma for names with comma
        pers = Person(sort_name='Casey, Jim')
        assert pers.short_name == 'Casey'
        # should return up to parenthesis for names with parenthesis
        pers = Person(sort_name='J.C. (Jim Casey)')
        assert pers.short_name == 'J.C.'
        # if both should return up to whichever is first - comma or paren
        pers = Person(sort_name='J.C. (Jim Casey, Esq.)')
        assert pers.short_name == 'J.C.'
        pers = Person(sort_name='Jim Casey, Esq. (J.C.)')
        assert pers.short_name == 'Jim Casey'
        # should just return the full name if neither
        pers.sort_name = 'Jim Casey'
        assert pers.short_name == 'Jim Casey'

    def test_set_birth_death_years(self):
        pers = Person(name='Humperdinck')
        # no viaf id
        pers.set_birth_death_years()
        assert pers.birth_year is None
        assert pers.death_year is None

        pers.viaf_id = 'http://viaf.org/viaf/35247539'
        with patch.object(Person, 'viaf') as mockviaf_entity:
            mockviaf_entity.birthyear = 1902
            mockviaf_entity.deathyear = 1953
            pers.set_birth_death_years()
            assert pers.birth_year == mockviaf_entity.birthyear
            assert pers.death_year == mockviaf_entity.deathyear

    def test_save(self):
        pers = Person(name='Humperdinck')
        with patch.object(pers, 'set_birth_death_years') as mock_setbirthdeath:
            # no viaf - should not call set birth/death
            pers.save()
            mock_setbirthdeath.assert_not_called()

            # viaf and dates set - should not call set birth/death
            pers.viaf_id = 'http://viaf.org/viaf/35247539'
            pers.birth_year = 1801
            pers.death_year = 1850
            pers.save()
            mock_setbirthdeath.assert_not_called()

            # viaf and one date set - should not call set birth/death
            pers.birth_year = None
            pers.save()
            mock_setbirthdeath.assert_not_called()

            # viaf and one date set - *should* call set birth/death
            pers.death_year = None
            pers.save()
            mock_setbirthdeath.assert_called_with()

    def test_address_count(self):

        # create a person
        pers = Person.objects.create(name='Foobar')
        # no addresses
        assert pers.address_count() == 0
        loc = Location.objects.create(name='L\'Hotel', city='Paris')

        # add an address
        Address.objects.create(location=loc, person=pers)
        # should be one
        assert pers.address_count() == 1

        # add another, should be 2
        loc2 = Location.objects.create(name='Elysian Fields', city='Paris')
        Address.objects.create(location=loc2, person=pers)
        assert pers.address_count() == 2

    def test_nationality_list(self):
        # create a person
        pers = Person.objects.create(name='Foobar')
        # no nationalities
        assert pers.list_nationalities() == ''
        country = Country.objects.create(name='France', code='FR')
        pers.nationalities.add(country)
        assert pers.list_nationalities() == 'France'
        # add spanish citizenship
        country = Country.objects.create(name='Spain', geonames_id='123')
        pers.nationalities.add(country)
        assert pers.list_nationalities() == 'France, Spain'

    def test_account_id(self):
        # create a person
        pers = Person.objects.create(name='Foobar')
        # create an account
        acct = Account.objects.create()
        # not associated so person has no account number
        assert pers.account_id() == ''
        # associate
        acct.persons.add(pers)
        assert pers.account_id() == acct.id

    def test_has_account(self):
        # create a person
        pers = Person.objects.create(name='Foobar')
        # create an account
        acct = Account.objects.create()
        # not associated, returns False
        assert not pers.has_account()
        # associate, should return True
        acct.persons.add(pers)
        assert pers.has_account()

    def test_subscription_dates(self):
        pers = Person.objects.create(name='Foo')
        acc = Account.objects.create()
        acc.persons.add(pers)
        sub1 = Subscription.objects.create(
            start_date=date(1950, 1, 5),
            end_date=date(1950, 1, 8),
            account=acc
        )
        sub2 = Subscription.objects.create(
            start_date=date(1950, 2, 10),
            account=acc
        )
        assert pers.subscription_dates() == '; '.join(s.date_range
                                                      for s in [sub1, sub2])

    def test_is_creator(self):
        # create a person
        pers = Person.objects.create(name='Foobar')
        # create an item and creator type
        work = Work(title='Le foo et le bar', year=1916, mep_id='lfelb')
        work.save()
        ctype = CreatorType(1)
        # not associated, returns False
        assert not pers.is_creator()
        # associate via Creator, should return True
        creator = Creator(creator_type=ctype, person=pers, work=work)
        creator.save()
        assert pers.is_creator()

    def test_in_logbooks(self):
        # create test person & account and associate them
        pers = Person.objects.create(name='John')
        # no account - not in logbooks
        assert not pers.in_logbooks()

        acct = Account.objects.create()
        acct.persons.add(pers)
        # account but no logbook events
        assert not pers.in_logbooks()

        # add subscription event
        subs = Subscription.objects.create(account=acct)
        assert pers.in_logbooks()

        # add reimbursment
        Reimbursement.objects.create(account=acct)
        assert pers.in_logbooks()

        # still true if only reimbursement and no subscription
        subs.delete()
        assert pers.in_logbooks()

    def test_admin_url(self):
        pers = Person.objects.create(name='John')
        resolved_url = resolve(pers.admin_url())
        assert resolved_url.args[0] == str(pers.id)
        assert resolved_url.view_name == 'admin:people_person_change'

    def test_has_card(self):
        # create test person & account and associate them
        pers = Person.objects.create(name='John')
        # no account, no card
        assert not pers.has_card()

        acct = Account.objects.create()
        acct.persons.add(pers)
        # account but no card
        assert not pers.has_card()

        # create card and add to account
        src_type = SourceType.objects.get_or_create(
            name='Lending Library Card')[0]
        card = Bibliography.objects.create(
            bibliographic_note='John\'s Library Card', source_type=src_type)
        acct.card = card
        acct.save()
        assert pers.has_card()

    def test_get_absolute_url(self):
        pers = Person.objects.create(name='John Smith')
        # none for non-member
        assert pers.get_absolute_url() is None

        # add account
        acct = Account.objects.create()
        acct.persons.add(pers)
        # uses pk for now
        assert pers.get_absolute_url() == \
            reverse('people:member-detail', args=[pers.pk])

    def test_index_data(self):
        pers = Person.objects.create(
            name='John Smith', sort_name='Smith, John', birth_year=1801,
            death_year=1847)
        # no account = minimal index data
        index_data = pers.index_data()
        assert index_data['id'] == pers.index_id()
        assert 'item_type' not in index_data
        assert len(index_data) == 1

        # add account
        acct = Account.objects.create()
        acct.persons.add(pers)
        index_data = pers.index_data()
        assert 'item_type' in index_data
        assert index_data['pk_i'] == pers.pk
        assert index_data['name_t'] == pers.name
        assert index_data['sort_name_t'] == pers.sort_name
        assert index_data['birth_year_i'] == pers.birth_year
        assert index_data['death_year_i'] == pers.death_year
        # account dates and sex should not be set
        for missing_val in ['account_start_i', 'account_end_i',
                            'account_years_i', 'sex_s']:
            assert missing_val not in index_data
        # nationality should be empty list
        assert index_data['nationality'] == []

        # add account events for earliest/latest
        Subscription.objects.create(account=acct,
                                    start_date=datetime.date(1921, 1, 1))
        Reimbursement.objects.create(account=acct,
                                     start_date=datetime.date(1922, 1, 1))
        # add sex information
        pers.sex = Person.MALE
        index_data = pers.index_data()
        assert index_data['account_start_i'] == 1921
        assert index_data['account_end_i'] == 1922
        assert index_data['account_years_is'] == [1921, 1922]
        assert index_data['sex_s'] == 'Male'

        # add nationality
        uk = Country.objects.create(
            name='United Kingdom', code='UK',
            geonames_id='http://sws.geonames.org/2635167/')
        denmark = Country.objects.create(
            name='Denmark', code='DK',
            geonames_id='http://sws.geonames.org/2623032/')
        pers.nationalities.add(uk)
        pers.nationalities.add(denmark)
        index_data = pers.index_data()
        assert uk.name in index_data['nationality']
        assert denmark.name in index_data['nationality']


class TestPersonQuerySet(TestCase):

    def test_library_members(self):
        jones = Person.objects.create(name='Jones')
        # person with no account = no members
        assert not Person.objects.library_members().exists()

        acct = Account.objects.create()
        acct.persons.add(jones)
        assert jones in Person.objects.library_members()

    def test_merge_with(self):
        # create test records to merge
        Person.objects.bulk_create([
            Person(name='Jones'),
            Person(name='Jones', title='Mr'),
            Person(name='Jonas'),
        ])

        # use Jonas as record to merge others to
        main_person = Person.objects.get(name='Jonas')

        # create accounts with content to merge
        main_acct = Account.objects.create()
        main_acct.persons.add(main_person)
        Subscription.objects.create(account=main_acct)

        # account with events and addresses
        mr_jones = Person.objects.get(name='Jones', title='Mr')
        mr_jones_acct = Account.objects.create()
        mr_jones_acct.persons.add(mr_jones)
        Subscription.objects.create(account=mr_jones_acct)
        Reimbursement.objects.create(account=mr_jones_acct)
        hotel = Location.objects.create(name="La Hotel", city="Paris")
        residence = Location.objects.create(name="52 La Rue", city="Paris")
        # account address
        acct_addr = Address.objects.create(location=hotel, account=mr_jones_acct)
        # person address
        mr_jones_addr = Address.objects.create(location=residence, person=mr_jones)

        # merge everything with Jonas
        Person.objects.merge_with(main_person)
        # should delete duplicate records
        assert Person.objects.count() == 1
        # automatically excludes merge person target from merge logic,
        # even if the record is included in the queryset
        assert Person.objects.filter(id=main_person.id).exists()
        # account events should be reassociated
        assert main_acct.event_set.count() == 3
        # account address should be reassociated
        assert main_acct.address_set.filter(id=acct_addr.id).exists()
        # person address should be reassociated
        assert mr_jones_addr in main_person.address_set.all()
        # accounts associated with merged persons should be gone
        assert not Account.objects.filter(id=mr_jones_acct.id).exists()

        # no mepids, but should still list that the merges occurred
        # get the current date for the string - used below
        iso_date = timezone.now().strftime('%Y-%m-%d')
        assert main_person.notes
        jones_str = 'Merged Jones on %s' % iso_date
        # Jones will appear twice from being merged into Jonas
        assert main_person.notes.count(jones_str) == 2

        # error on attempt to merge to person with multiple accounts
        second_acct = Account.objects.create()
        second_acct.persons.add(main_person)
        with pytest.raises(MultipleObjectsReturned) as excinfo:
            Person.objects.merge_with(main_person)
        assert "Can't merge with a person record that has multiple accounts" \
            in str(excinfo.value)
        main_person.delete()

        # copy person details when merging
        main = Person.objects.create(name='Jones')
        prof = Profession.objects.create(name='Professor')
        full = Person.objects.create(
            name='Jones',
            title='Mr', mep_id="jone.mi", birth_year=1901, death_year=1950,
            viaf_id='http://viaf.org/viaf/123456', sex='M',
            notes='some details', profession=prof)
        acct = Account.objects.create()
        acct.persons.add(main)

        # values should copy over to main fields
        Person.objects.merge_with(main)
        # get fresh copy of main record from db
        main = Person.objects.get(id=main.id)
        assert main.title == full.title
        assert main.mep_id == full.mep_id
        assert main.birth_year == full.birth_year
        assert main.death_year == full.death_year
        assert main.sex == full.sex
        assert main.viaf_id == full.viaf_id
        assert main.profession == full.profession
        assert full.notes in main.notes
        assert 'Merged MEP id %s on %s' % (full.mep_id, iso_date) in main.notes

        # should _not_ copy over existing field values
        full2 = Person.objects.create(
            name='Jones', title='Dr', mep_id="jone.dr", birth_year=1911,
            notes='more details')
        Person.objects.merge_with(main)
        # get fresh copy of main record from db
        main = Person.objects.get(id=main.id)
        assert main.title != full2.title
        assert main.mep_id != full2.mep_id
        assert main.birth_year != full2.birth_year
        # notes should be appended
        assert full.notes in main.notes
        assert full2.notes in main.notes
        assert 'Merged MEP id %s on %s' % (full2.mep_id, iso_date) \
            in main.notes

        # many-to-many relationships should be shifted to merged person record
        related = Person.objects.create(name='Jonesy')
        jones_jr = Person.objects.create(name='Jonesy Jr.')
        france = Country.objects.create(
            name='France', code='fr', geonames_id='http://www.geonames.org/3017382/')
        germany = Country.objects.create(
            name='Germany', code='gm', geonames_id='http://www.geonames.org/2921044/')
        related.nationalities.add(france, germany)
        info_url = InfoURL.objects.create(
            person=related, url='http://example.com/')
        info_url2 = InfoURL.objects.create(
            person=related, url='http://google.com/')
        child = RelationshipType.objects.create(name='child')
        parent = RelationshipType.objects.create(name='parent')
        child_rel = Relationship.objects.create(
            from_person=related, to_person=jones_jr, relationship_type=child)
        parent_rel = Relationship.objects.create(
            from_person=jones_jr, to_person=related, relationship_type=parent)
        # footnote
        src_type = SourceType.objects.create(name='website')
        bibl = Bibliography.objects.create(
            bibliographic_note='citation', source_type=src_type)
        person_contenttype = ContentType.objects.get_for_model(Person)
        fn = Footnote.objects.create(
            bibliography=bibl, content_type=person_contenttype,
            object_id=related.pk, is_agree=False)

        Person.objects.filter(name='Jonesy').merge_with(main)
        # get fresh copy of main record from db
        main = Person.objects.get(id=main.id)
        assert france in main.nationalities.all()
        assert germany in main.nationalities.all()
        assert info_url in main.urls.all()
        assert info_url2 in main.urls.all()
        assert child_rel in main.from_relationships.all()
        assert parent_rel in main.to_relationships.all()
        assert fn in main.footnotes.all()

        # person with account shared with another person
        sib1 = Person.objects.create(name='sibling')
        sib2 = Person.objects.create(name='sibling2')
        acct = Account.objects.create()
        acct.persons.add(sib1, sib2)

        with pytest.raises(MultipleObjectsReturned) as excinfo:
            Person.objects.merge_with(main)
        assert "Can't merge a person record with a shared account." in \
            str(excinfo.value)

        # merging a person who is a creator should change their items to point
        # to the new person as creator
        mike = Person.objects.create(name='Mike Mulshine')
        spencer = Person.objects.create(name='Spencer Hadley')
        nikitas = Person.objects.create(name='Nikitas Tampakis')
        book1 = Work.objects.create()
        book2 = Work.objects.create()
        author = CreatorType.objects.get(name='Author')
        editor = CreatorType.objects.get(name='Editor')
        # spencer author of book1
        Creator.objects.create(creator_type=author, person=spencer, work=book1)
        # nikitas editor of book2
        Creator.objects.create(creator_type=editor, person=nikitas, work=book2)
        # spencer author of book2
        Creator.objects.create(creator_type=author, person=spencer, work=book2)
        qs = Person.objects.filter(pk=spencer.id) | \
            Person.objects.filter(pk=nikitas.id)
        qs.merge_with(mike)
        assert mike in book1.authors
        assert mike in book2.authors
        assert mike in book2.editors
        assert spencer not in book1.authors
        assert spencer not in book2.authors
        assert nikitas not in book2.editors

        # main person with no account data should receive the first merged
        # account & all subsequent events/addresses will merge to that account
        mike = Person.objects.create(name='Mike Mulshine')
        spencer = Person.objects.create(name='Spencer Hadley', birth_year=1990)
        nikitas = Person.objects.create(name='Nikitas Tampakis')
        spencer_acct = Account.objects.create()
        spencer_acct.persons.add(spencer)
        location = Location.objects.create()
        spencer_address = Address.objects.create(account=spencer_acct,
                                                 location=location)
        spencer_event = Subscription.objects.create(account=spencer_acct)
        nikitas_acct = Account.objects.create()
        nikitas_acct.persons.add(nikitas)
        nikitas_address = Address.objects.create(account=nikitas_acct,
                                                 location=location)
        nikitas_event = Subscription.objects.create(account=nikitas_acct)
        qs = Person.objects.filter(pk__in=[spencer.id, nikitas.id])
        qs.merge_with(mike)
        assert mike.name == 'Mike Mulshine'  # kept set properties
        assert mike.birth_year == 1990  # merged new properties
        assert spencer_acct in mike.account_set.all()  # first account was used
        # subsequent ones were deleted
        assert nikitas_acct not in mike.account_set.all()
        # addresses were merged
        assert spencer_address in mike.account_set.first().address_set.all()
        assert nikitas_address in mike.account_set.first().address_set.all()
        # events were merged
        assert spencer_event in \
            mike.account_set.first().get_events(etype='subscription')
        assert nikitas_event in \
            mike.account_set.first().get_events(etype='subscription')

        # merge a record with associated card bibliography to
        # a record without should copy the card
        nicholas = Person.objects.create(name='Nicholas')
        src_type = SourceType.objects.get_or_create(
            name='Lending Library Card')[0]
        card = Bibliography.objects.create(
            bibliographic_note='Nicholas\' library card, North Pole Library',
            source_type=src_type)
        nicholas_acct = Account.objects.create(card=card)
        nicholas_acct.persons.add(nicholas)
        qs = Person.objects.filter(pk=nicholas.id)
        assert not mike.has_card()
        qs.merge_with(mike)
        assert mike.account_set.first().card
        assert mike.has_card()

        # merging a record with a card to another record with a card
        # should log a warning
        john = Person.objects.create(name='John')
        card = Bibliography.objects.create(
            bibliographic_note='John\'s library card', source_type=src_type)
        john_acct = Account.objects.create(card=card)
        john_acct.persons.add(john)
        qs = Person.objects.filter(pk=john.id)
        assert mike.has_card()
        with self.assertLogs('mep', level='WARN') as logs:
            qs.merge_with(mike)
            # mike's existing card should not be overwritten with john's card
            assert mike.account_set.first().card != card
        assert 'association will be lost in merge' in logs.output[0]


class TestRelationship(TestCase):

    def setUp(self):
        self.foo = Person.objects.create(name='Foo')
        self.foo_bro = Person.objects.create(name='Bar')
        self.relationshiptype = RelationshipType.objects.create(name='sibling')
        self.relationship = Relationship.objects.create(
            from_person=self.foo,
            to_person=self.foo_bro,
            relationship_type=self.relationshiptype
        )

    def test_relationship_str(self):
        assert str(self.relationship) == 'Foo is a sibling to Bar.'

    def test_relationship_repr(self):
        assert repr(self.relationship) == (
            "<Relationship {'from_person': <Person Foo>, "
            "'to_person': <Person Bar>, "
            "'relationship_type': <RelationshipType sibling>}>"
        )


class TestRelationshipM2M(TestCase):

    def setUp(self):
        self.foo = Person.objects.create(name='Foo')
        self.bar = Person.objects.create(name='Bar')
        self.parent = RelationshipType.objects.create(name='parent')
        Relationship.objects.create(
            from_person=self.foo,
            to_person=self.bar,
            relationship_type=self.parent
        )

        self.baz = Person.objects.create(name='Baz')
        self.partner = RelationshipType.objects.create(name='business partner')

        Relationship.objects.create(
            from_person=self.foo,
            to_person=self.baz,
            relationship_type=self.partner
        )

    def test_relationships(self):
        # Relationship is one sided based on from_person and to_person
        # With the relationship 'parent'

        # foo is parent of bar - should get Foo
        assert Person.objects \
                     .get(from_relationships__relationship_type=self.parent) \
            == self.foo
        # reverse - should get Bar
        assert Person.objects \
                     .get(to_relationships__relationship_type=self.parent) \
            == self.bar
        # foo is partner of bas - should get Baz
        assert Person.objects \
                     .get(to_relationships__relationship_type=self.partner) \
            == self.baz

        # foo is related to both Bar and Baz, so length of 2
        assert len(self.foo.relations.all()) == 2
        # Should still be two if we filter out only Bar and Baz
        # Short way to check if both and only both are in the query set
        assert len(self.foo.relations.filter(name__in=['Baz', 'Bar'])) \
            == 2


class TestAddress(TestCase):

    def test_str(self):
        # Name and city only
        address = Location(name="La Hotel", city="Paris")
        assert str(address) == "La Hotel, Paris"

        # street and city only
        address = Location(street_address="1 Rue Le Foo", city="Paris")
        assert str(address) == "1 Rue Le Foo, Paris"

        # Name, street, and city
        address = Location(
            street_address="1 Rue Le Foo", city="Paris", name="La Hotel")
        assert str(address) == "La Hotel, 1 Rue Le Foo, Paris"

        # city only
        address = Location(city="Paris")
        assert str(address) == "Paris"

    def test_repr(self):
        hotel = Location(name='La Hotel', city='Paris')
        assert repr(hotel).startswith('<Location ')
        assert repr(hotel).endswith('>')
        assert hotel.name in repr(hotel)
        assert hotel.city in repr(hotel)

    def test_latlon_validate(self):
        # Valid, should pass clean fields
        address = Location(latitude=180, longitude=-180, city="Paris")
        address.clean_fields()

        # Not valid, should error out
        with pytest.raises(ValidationError) as excinfo:
            address.latitude = -500
            address.clean_fields()
        assert "Lat/Lon must be between -180 and 180 degrees." in \
            str(excinfo.value)

        # String should error out too, Django handles the message
        address = Location(latitude="foo", longitude="bar")
        with pytest.raises(ValidationError):
            address.clean_fields()


class TestInfoURL(TestCase):

    def test_str(self):
        pers = Person.objects.create(name='Someone')
        info_url = InfoURL(person=pers, url='http://example.com/')
        assert str(info_url) == info_url.url

    def test_repr(self):
        pers = Person.objects.create(name='Someone')
        info_url = InfoURL(person=pers, url='http://example.com/')
        # unsaved
        assert repr(info_url) == '<InfoURL pk:?? %s>' % info_url.url
        # saved
        info_url.save()
        assert repr(info_url) == '<InfoURL pk:%s %s>' % \
            (info_url.pk, info_url.url)
