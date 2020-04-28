from parasolr import schema


class SolrTextField(schema.SolrTypedField):
    field_type = 'text_en'


class SolrSchema(schema.SolrSchema):
    '''Solr Schema declaration.'''

    item_type = schema.SolrStringField()

    nationality = schema.SolrStringField(multivalued=True)
    edition_titles = SolrTextField(multivalued=True)

    # relying on dynamic fields for everything else; see index_data
    # methods and solr queryset aliases for specifics

    #: copy fields for facets and variant search options
    copy_fields = {
        # ngram version of names for searching
        'name_t': 'name_ngram',
        'sort_name_t': 'name_ngram',
        # stemmed version of titles for searching
        'title_t': 'title_txt_en',
    }
