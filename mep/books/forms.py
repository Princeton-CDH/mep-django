from django import forms

from mep.common.forms import FacetForm, RangeField, RangeWidget, \
    SelectWithDisabled


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
    circulation_dates = RangeField(label='Circulation Dates', required=False,
                                   widget=RangeWidget(attrs={'size': 4}))

    # copied from member search form
    def set_range_minmax(self, range_minmax):
        '''Set the min, max, and placeholder values for all
        :class:`~mep.common.forms.RangeField` instances.

        :param range_minmax: a dictionary with form fields as key names and
            tuples of min and max integers as values.
        :type range_minmax: dict

        :rtype: None
        '''
        for field_name, min_max in range_minmax.items():
            self.fields[field_name].set_min_max(min_max[0], min_max[1])

    def __init__(self, data=None, *args, **kwargs):
        '''
        Override to set choices dynamically and configure min-max range values
        based on form kwargs.
        '''
        # pop range_minmax out of kwargs to avoid clashing
        # with django args
        range_minmax = kwargs.pop('range_minmax', {})

        super().__init__(data=data, *args, **kwargs)

        # call function to set min_max and placeholders
        self.set_range_minmax(range_minmax)
