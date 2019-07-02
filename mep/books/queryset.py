from parasolr.django import AliasedSolrQuerySet


class ItemSolrQuerySet(AliasedSolrQuerySet):
    """':class:`~parasolr.django.AliasedSolrQuerySet` for
    :class:`~mep.book.models.Item`"""

    #: always filter to item records
    filter_qs = ['item_type:item']

    #: map readable field names to actual solr fields
    field_aliases = {
        'title': 'title_s',
        'authors': 'authors_t',
        'editors': 'editors_t',
        'pub_date': 'pub_date_i',
        'translators': 'translators_t',
        'pk': 'pk_i',
        'account_start': 'account_start_i',
        'account_end': 'account_end_i'
    }
