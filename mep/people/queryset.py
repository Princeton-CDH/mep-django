from parasolr.django import AliasedSolrQuerySet


class PersonSolrQuerySet(AliasedSolrQuerySet):
    """':class:`~parasolr.django.AliasedSolrQuerySet` for
    :class:`~mep.people.models.Person`"""

    #: always filter to person records
    filter_qs = ['item_type:person']

    #: map readable field names to actual solr fields
    field_aliases = {
        'name': 'name_t',
        'sort_name': 'sort_name_t',
        'birth_year': 'birth_year_i',
        'death_year': 'death_year_i',
        'account_start': 'account_start_i',
        'account_end': 'account_end_i',
        'account_years': 'account_years_is',
        'account_yearmonths': 'account_yearmonths_is',
        'logbook_yearmonths': 'logbook_yearmonths_is',
        'card_yearmonths': 'card_yearmonths_is',
        'has_card': 'has_card_b',
        'pk': 'pk_i',
        'gender': 'gender_s',
    }
