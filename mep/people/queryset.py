from parasolr.django import SolrQuerySet



class PersonSolrQuerySet(SolrQuerySet):
    #: always filter to person records
    filter_qs = ['item_type:person']

    #: map app/readable field names to actual solr fields
    field_aliases = {
        'name': 'name_t',
        'sort_name':'sort_name_t',
        'birth_year':'birth_year_i',
        'death_year':'death_year_i',
        'account_start':'account_start_i',
        'account_end':'account_end_i',
        'has_card':'has_card_b',
        'pk':'pk_i'
    }

    #: default field list generated from field_aliases
    field_list = ['%s:%s' % (key, value)
                  for key, value in field_aliases.items()]

    def _unalias_args(self, *args):
        # convert alias name to solr field for list of args
        return [self.field_aliases.get(arg, arg) for arg in args]

    def _unalias_kwargs(self, **kwargs):
        # convert alias name to solr field for keys in kwaargs
        return {self.field_aliases.get(key, key): val
                for key, val in kwargs.items()}

    def _unalias_kwargs_with_lookups(self, **kwargs):
        # convert alias name to solr field for keys in kwaargs
        #  with support for __ lookups for filters
        new_kwargs = {}
        for key, val in kwargs.items():
            field_parts = key.split('__', 1)
            field = self.field_aliases.get(field, field)
            if len(field_parts) > 1:
                field = '%s__%s' % (field, field_parts[1])
            new_kwargs[field] = val

        return new_kwargs

    # should get facets map solr field back to alias?
    # def get_facets(self) -> Dict[str, int]:

    def filter(self, *args, **kwargs) -> 'PersonSolrQuerySet':
        args = self._unalias_args(*args)
        kwargs = self._unalias_kwargs_with_lookups(**kwargs)
        return super().filter(*args, **kwargs)

    def facet(self, *args: str, **kwargs) -> 'PersonSolrQuerySet':
        args = self._unalias_args(*args)
        kwargs = self._unalias_kwargs(**kwargs)
        return super().facet(*args, **kwargs)

    def facet_field(self, field: str, **kwargs) -> 'PersonSolrQuerySet':
        field = self.field_aliases.get(field, field)
        return super().facet(field, **kwargs)

    def order_by(self, *args) -> 'PersonSolrQuerySet':
        args = self._unalias_args(*args)
        return super().order_by(*args)

    def only(self, *args, **kwargs) -> 'PersonSolrQuerySet':
        args = self._unalias_args(*args)
        return super().filter(*args, **kwargs)

    def highlight(self, field: str, **kwargs) -> 'PersonSolrQuerySet':
        field = self.field_aliases.get(field, field)
        return super().highlight(field, **kwargs)

    # should get highlighting map solr field back to alias?
    # def get_highlighting(self):