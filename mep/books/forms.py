from django import forms

from mep.common.forms import FacetForm, SelectWithDisabled


class WorkSearchForm(FacetForm):
    '''Book search form'''

    SORT_CHOICES = [
        ('title', 'Title A – Z'),
        ('title_za', 'Title Z – A'),
        ('author', 'Author A – Z'),
        ('author_za', 'Author Z – A'),
        ('borrowing_desc', 'Borrowing Frequency Highest – Lowest'),
        ('borrowing', 'Borrowing Frequency Lowest – Highest'),
        ('pubdate', 'Publication Date Oldest – Newest'),
        ('pubdate_desc', 'Publication Date Newest – Oldest'),
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
