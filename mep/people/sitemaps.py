from datetime import date

from django.contrib.sitemaps import Sitemap
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

    def items(self):
        # find canvas objects associated with members via account cards
        return Canvas.objects \
            .filter(manifest__bibliography__account__isnull=False) \
            .values('short_id',
                    'manifest__bibliography__account__persons__slug') \
            .distinct()
        # NOTE: this does not include the handful of cards that appear
        # at more than one url, because a member has an event on someone
        # else's card

    def location(self, obj):
        return reverse(self.url_route, kwargs={
            'slug': obj['manifest__bibliography__account__persons__slug'],
            'short_id': obj['short_id']
        })

    # Not sure how to calculate last modified; member last indexed
    # in Solr is probably a decent proxy, but requires a separate query
    # (and also doesn't account for card image changes)
