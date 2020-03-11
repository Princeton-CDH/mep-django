from parasolr.django import AliasedSolrQuerySet


class WorkSolrQuerySet(AliasedSolrQuerySet):
    """':class:`~parasolr.django.AliasedSolrQuerySet` for
    :class:`~mep.book.models.Item`"""

    #: always filter to item records
    filter_qs = ['item_type:work']

    #: map readable field names to actual solr fields
    field_aliases = {
        'title': 'title_t',
        'sort_title': 'sort_title_isort',
        'authors': 'authors_t',
        'creators': 'creators_t',
        'pub_date': 'pub_date_i',
        'format': 'format_s',
        'pk': 'pk_i',
        'notes': 'notes_txt_en',
        'account_start': 'account_start_i',
        'account_end': 'account_end_i'
    }
