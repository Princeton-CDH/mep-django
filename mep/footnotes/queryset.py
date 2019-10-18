from parasolr.django import AliasedSolrQuerySet


class CardSolrQuerySet(AliasedSolrQuerySet):
    """':class:`~parasolr.django.AliasedSolrQuerySet` for
    :class:`~mep.footnotes.models.Bibliography` records indexed
    as lending library cadrs"""

    #: always filter to card records
    filter_qs = ['item_type:card']

    #: map readable field names to actual solr fields
    field_aliases = {
        'cardholder': 'cardholder_t',
        'cardholder_sort': 'cardholder_sort_s',
        'start': 'card_start_i',
        'end': 'card_end_i',
        'years': 'card_years_is',
        'thumbnail': 'thumbnail_t',
        'thumbnail2x': 'thumbnail2x_t',
    }
