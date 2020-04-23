from django import forms

from mep.common.forms import FacetForm, SelectWithDisabled


class WorkSearchForm(FacetForm):
    '''Book search form'''

    SORT_CHOICES = [
        ('title', 'Title A – Z'),
        ('author', 'Author A – Z'),
        ('pubdate', 'Publication Date (Newest – Oldest)'),
        ('circulation_date', 'Circulation Date (Oldest – Newest)'),
        ('circulation', 'Circulation (Highest – Lowest)'),
        ('relevance', 'Relevance'),
    ]

    # NOTE these are not set by default!
    error_css_class = 'error'
    required_css_class = 'required'

    query = forms.CharField(
        label='Keyword or Phrase', required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search book',
            'aria-label': 'Keyword or Phrase'
        }))
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False,
                             widget=SelectWithDisabled)
