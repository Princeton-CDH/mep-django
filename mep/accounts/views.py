from dal import autocomplete
from django.db.models import Q
from django.http import JsonResponse

from mep.accounts.models import Account
from mep.accounts.queryset import AddressSolrQuerySet
from mep.people.views import MembersList


class AddressList(MembersList):
    '''JSON-only view. Returns addresses and members for display
    map display; honors all the same filters and search options
    as :class:`~mep.people.views.MembersList`.'''

    # solr member name fields for keyword se
    name_search_fields = ['name_t', 'sort_name_t', 'name_ngram']

    def get_queryset(self):
        # MembersList get_queryset returns a person solr queryset
        # filtered according to query params in the request
        members = super().get_queryset()
        addresses = AddressSolrQuerySet().all()

        # NOTE: handle search term specifically, since
        # qf name query doesn't work with the join query.
        # Search terms and raw query parameters on the members
        # quereset are ignored.
        search_term = self.request.GET.get('query', None)
        if search_term:
            # if there is a search term, join addresses on member slug to
            # find address by member
            # the member list view uses !qf notation, but that can't be
            # combined with the join; convert to an OR search on all
            # included fields, since we don't care about score here
            name_search = ' OR '.join('%s:(%s)' % (field, search_term)
                                      for field in self.name_search_fields)
            addresses = addresses \
                .search('{!join from=slug_s to=member_slug_ss v=$name_q}') \
                .raw_query_parameters(name_q=name_search)

        # apply all filters on the member queryset except item type,
        # and use the join syntax to find addresses for members who
        # are returned by those filters
        addresses.filter_qs.extend([
            '{!join from=slug_s to=member_slug_ss}%s' % filterq
            for filterq in members.filter_qs
            if not filterq.startswith('item_type:')
        ])

        # revise the member list queryset
        # - clear facets needed for member view (not needed here)
        # - restrict to members with an address via join query
        # - only return fields needed for member tile display
        members = members.facet() \
            .search('{!join to=slug_s from=member_slug_ss}*:*') \
            .only('sort_name', 'account_years', 'has_card', 'slug')

        self.addresses = addresses
        return members

    def render_to_response(self, request, *args, **kwargs):
        # convert member results from Slor into a dictionary keyed on slug
        members = dict((m['slug'], m) for m in
                       self.object_list.get_results(rows=10000))
        # TODO:
        # - if displaying consolidated membership years, convert here
        return JsonResponse({
            'numFound': {
                'addresses': self.addresses.count(),
                'members': self.object_list.count()
            },
            'addresses': list(self.addresses),
            'members': members
        })


class AccountAutocomplete(autocomplete.Select2QuerySetView):
    '''Basic autocomplete lookup, for use with django-autocomplete-light and
    :class:`mep.accounts.models.Account` in address many-to-many'''

    def get_queryset(self):
        '''Get a queryset filtered by query string. Searches on account id,
        people associated with account, and addresses associated with account
        '''

        return Account.objects.filter(
            Q(id__contains=self.q) |
            Q(persons__name__icontains=self.q) |
            Q(persons__mep_id__icontains=self.q) |
            Q(locations__name__icontains=self.q) |
            Q(locations__street_address__icontains=self.q) |
            Q(locations__city__icontains=self.q)
        ).distinct().order_by('id')
