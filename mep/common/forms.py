from typing import Any, Mapping

from django import forms
from django.utils.text import mark_safe

class CheckboxFieldset(forms.CheckboxSelectMultiple):

    template_name = 'common/widgets/checkbox_fieldset.html'


class FacetChoiceField(forms.MultipleChoiceField):
    '''Add CheckboxSelectMultiple field with facets taken from solr query'''
    # Borrowed from https://github.com/Princeton-CDH/derrida-django/blob/develop/derrida/books/forms.py
    # customize multiple choice field for use with facets.
    # no other adaptations needed
    # - turn off choice validation (shouldn't fail if facets don't get loaded)
    # - default to not required
    # - use checkbox select multiple as default widget

    widget = CheckboxFieldset


    def __init__(self, *args, **kwargs):
        if 'required' not in kwargs:
            kwargs['required'] = False
        super().__init__(*args, **kwargs)

        if self.label:
            self.widget.attrs['name'] = self.label.lower()

    def valid_value(self, value: Any) -> True:
        return True


class FacetForm(forms.Form):
    '''Form mixin to support mapping facet fields to
    :class`FacetChoiceField` fields.'''

    #: A mapping of facets fields to form fields.
    solr_facet_fields = {}

    def set_choices_from_facets(self, facets: Mapping[str, int]) -> None:
        '''Render a set of choices based on a mapping of facets to counts.'''
        # configure field choices based on facets returned from Solr
        # (adapted from derrida and winthrop codebase)
        for facet, counts in facets.items():
            # use field from facet fields map or else field name as is
            formfield = self.solr_facet_fields.get(facet, facet)
            if formfield in self.fields:
                self.fields[formfield].choices = [
                    (val, mark_safe('<span class="label">%s</span> '
                                    '<span class="count">%d</span>' %
                     (val if val else 'Unknown', count)))
                     for val, count in counts.items()
                ]

