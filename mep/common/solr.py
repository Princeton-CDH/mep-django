from parasolr import schema


class SolrSchema(schema.SolrSchema):
    '''Solr Schema declaration.'''

    item_type = schema.SolrStringField()

    nationality = schema.SolrStringField(multivalued=True)

    # relying on dynamic fields for now
