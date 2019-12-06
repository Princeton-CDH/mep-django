from parasolr import schema


class SolrSchema(schema.SolrSchema):
    '''Solr Schema declaration.'''

    item_type = schema.SolrStringField()

    nationality = schema.SolrStringField(multivalued=True)

    # relying on dynamic fields for everything else; see index data
    # methods and solr queryset aliases for specifics

    #: copy fields for facets and variant search options
    copy_fields = {
        # _s_en = string version of sort name for sort/facet
        # _txt_gen = unicode/case folding version for searching / sorting
        # _ngram = ngram tokenized version for partial matching
        'sort_name_t': 'name_ngram',
        'name_t': 'name_ngram'
    }
