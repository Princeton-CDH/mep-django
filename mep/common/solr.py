from parasolr import schema


class SolrSchema(schema.SolrSchema):
    '''Solr Schema declaration.'''

    item_type = schema.SolrStringField()

    nationality = schema.SolrStringField(multivalued=True)

    # relying on dynamic fields for everything else; see index data
    # methods and solr queryset aliases for specifics

    #: copy fields for facets and variant search options
    copy_fields = {
        # string version of sort name for sort/facet
        'sort_name_t': 'sort_name_sort_s_en',
        # unicode/case folding version of names for searching
        'name_t': 'name_txt_gen',
        'sort_name_t': 'name_txt_gen',
        # ngram version of names for searching
        'name_t': 'name_ngram',
        'sort_name_t': 'name_ngram',
    }
