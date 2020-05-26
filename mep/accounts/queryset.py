from parasolr.django import AliasedSolrQuerySet


class AddressSolrQuerySet(AliasedSolrQuerySet):
    """':class:`~parasolr.django.AliasedSolrQuerySet` for
    :class:`~mep.accounts.models.Address`"""

    #: always filter
    filter_qs = ['item_type:address']

    #: map readable field names to actual solr fields
    field_aliases = {
        'name': 'name_s',
        'street_address': 'street_address_s',
        'city': 'city_s',
        'postal_code': 'postal_code_s',
        'latitude': 'latitude_f',
        'longitude': 'longitude_f',
        'member_slugs': 'member_slug_ss',
        'arrondissement': 'arrondissement_i'
    }
