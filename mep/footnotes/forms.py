from django import forms

from mep.common.forms import FacetForm, SelectWithDisabled


class CardSearchForm(FacetForm):
    '''Card search form'''

    SORT_CHOICES = [
        ('relevance', 'Relevance'),
        ('name', 'Name A-Z'),
    ]

    # NOTE these are not set by default!
    error_css_class = 'error'
    required_css_class = 'required'

    query = forms.CharField(
        label='Keyword or Phrase', required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by library member',
            'aria-label': 'Keyword or Phrase'
        }))
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False,
                             widget=SelectWithDisabled)
