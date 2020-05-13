from datetime import date

from django.contrib.sitemaps import Sitemap
from django.db.models import F
from django.urls import reverse
from djiffy.models import Canvas

from mep.people.queryset import PersonSolrQuerySet


def solr_timestamp_to_date(timestamp):
    '''Convert solr isoformat date time string to python date.'''
    # format: 2020-05-12T15:46:20.341Z
    # django sitemap only includes date, so strip off time
    yearmonthday = timestamp.split('T')[0]
    return date(*[int(val) for val in yearmonthday.split('-')])


class MemberSitemap(Sitemap):
    url_route = 'people:member-detail'

    def items(self):
        return PersonSolrQuerySet().all().only('slug', 'last_modified')

    def location(self, obj):
        return reverse(self.url_route, kwargs={'slug': obj['slug']})

    def lastmod(self, obj):
        return solr_timestamp_to_date(obj['last_modified'])

    # NOTE: could set variable priority based on record completeness,
    # e.g. has card, viaf link, etc.


# NOTE: solr index is updated when events change, so member last modified
# can be used for all associated member pages


class MembershipActivitiesSitemap(MemberSitemap):
    url_route = 'people:membership-activities'

    # NOTE: set low priority for member with no membership activities


class BorrowingActivitiesSitemap(MemberSitemap):
    url_route = 'people:borrowing-activities'

    # NOTE: set low priority for member with no borrowing activities


class MemberCardListSitemap(MemberSitemap):
    url_route = 'people:member-card-list'

    # NOTE: set low priority for member with no cards


class MemberCardDetailSitemap(Sitemap):
    url_route = 'people:member-card-detail'

    members_lastmod = None

    def items(self):
        # query solr for member last modified dates
        solr_lastmod = PersonSolrQuerySet().filter(has_card=True) \
            .only('slug', 'last_modified').get_results(rows=10000)
        # last modified date lookup dict keyed on member slug
        self.members_lastmod = dict(
            (d['slug'], solr_timestamp_to_date(d['last_modified']))
            for d in solr_lastmod)
        # find canvas objects associated with members via account cards
        return Canvas.objects \
            .filter(manifest__bibliography__account__isnull=False) \
            .annotate(slug=F('manifest__bibliography__account__persons__slug')) \
            .values('short_id', 'slug') \
            .distinct()
        # NOTE: this does not include the handful of cards that appear
        # at more than one url, because a member has an event on someone
        # else's card

    def location(self, obj):
        return reverse(self.url_route, kwargs={
            'slug': obj['slug'],
            'short_id': obj['short_id']
        })

    def lastmod(self, obj):
        # using member last indexed in Solr as proxy, should
        # reflect any member event changes
        # (doesn't account for card image changes)
        return self.members_lastmod.get(obj['slug'], None)
