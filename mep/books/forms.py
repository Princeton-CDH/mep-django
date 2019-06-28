from django import forms

from mep.common.forms import FacetForm, SelectWithDisabled


class ItemSearchForm(FacetForm):
    '''Book search form'''

    SORT_CHOICES = [
        ('relevance', 'Relevance'),
        ('title', 'Title A-Z'),
    ]

    # NOTE these are not set by default!
    error_css_class = 'error'
    required_css_class = 'required'

    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False,
                             widget=SelectWithDisabled)
