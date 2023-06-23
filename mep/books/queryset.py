from parasolr.django import AliasedSolrQuerySet


class WorkSolrQuerySet(AliasedSolrQuerySet):
    """':class:`~parasolr.django.AliasedSolrQuerySet` for
    :class:`~mep.book.models.Item`"""

    #: always filter to item records
    filter_qs = ["item_type:work"]

    #: map readable field names to actual solr fields
    field_aliases = {
        "pk": "pk_i",
        "title": "title_t",
        "sort_title": "sort_title_isort",
        "authors": "authors_t",
        "sort_authors": "sort_authors_t",
        "creators": "creators_t",
        "pub_date": "pub_date_i",
        "format": "format_s_lower",
        "slug": "slug_s",
        "notes": "notes_txt_en",
        "account_start": "account_start_i",
        "account_end": "account_end_i",
        "is_uncertain": "is_uncertain_b",
        "event_count": "event_count_i",
        "event_years": "event_years_is",
    }

    # edismax alias for searching on admin work pseudo-field
    admin_work_qf = "{!type=edismax qf=$admin_work_qf pf=$admin_work_pf v=$work_query}"

    def search_admin_work(self, search_term):
        return self.search(self.admin_work_qf).raw_query_parameters(
            work_query=search_term
        )
