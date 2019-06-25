from django import forms
from django.template.loader import get_template

from mep.common.forms import FacetChoiceField, FacetForm, CheckboxFieldset, \
    RangeField, RangeWidget
from django.core.cache import cache
from mep.people.models import Person
from mep.people.queryset import PersonSolrQuerySet


class PersonChoiceField(forms.ModelChoiceField):
    label_template = get_template('people/snippets/person_option_label.html')

    def label_from_instance(self, person):
        return self.label_template.render({'person': person})


class PersonMergeForm(forms.Form):
    primary_person = PersonChoiceField(
        label='Primary record', queryset=None,
        help_text='Select the person record to preserve. ' +
                  'All events from other people will be reassociated with ' +
                  'their account.',
        empty_label=None, widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        person_ids = kwargs.get('person_ids', [])
        try:
            del kwargs['person_ids']
        except KeyError:
            pass

        super().__init__(*args, **kwargs)
        self.fields['primary_person'].queryset = \
            Person.objects.filter(id__in=person_ids)


## SelectDisabledMixin borrowed from ppa-django


class SelectDisabledMixin(object):
    '''
    Mixin for :class:`django.forms.RadioSelect` or :class:`django.forms.CheckboxSelect`
    classes to set an option as disabled. To disable, the widget's choice
    label option should be passed in as a dictionary with `disabled` set
    to True::

        {'label': 'option', 'disabled': True}.
    '''

    # Using a solution at https://djangosnippets.org/snippets/2453/
    def create_option(self, name, value, label, selected, index, subindex=None,
                      attrs=None):
        disabled = None

        if isinstance(label, dict):
            label, disabled = label['label'], label.get('disabled', False)
        option_dict = super().create_option(
            name, value, label, selected, index,
            subindex=subindex, attrs=attrs
        )
        if disabled:
            option_dict['attrs'].update({'disabled': 'disabled'})
        return option_dict


class RadioSelectWithDisabled(SelectDisabledMixin, forms.RadioSelect):
    '''
    Subclass of :class:`django.forms.RadioSelect` with option to mark
    a choice as disabled.
    '''


class SelectWithDisabled(SelectDisabledMixin, forms.Select):
    '''
    Subclass of :class:`django.forms.Select` with option to mark
    a choice as disabled.
    '''


class MemberSearchForm(FacetForm):
    '''Member search form'''

    SORT_CHOICES = [
        ('relevance', 'Relevance'),
        ('name', 'Name A-Z'),
    ]


    # NOTE these are not set by default!
    error_css_class = 'error'
    required_css_class = 'required'

    query = forms.CharField(label='Keyword or Phrase', required=False,
                            widget=forms.TextInput(attrs={
                                'placeholder': 'Search member',
                                'aria-label': 'Keyword or Phrase'
                            }))
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False,
                             widget=SelectWithDisabled)
    has_card = forms.BooleanField(
        label='Card', required=False,
        widget=forms.CheckboxInput(attrs={
            'aria-label': 'Card',
            'aria-describedby': 'has_card_tip'
        }),
        help_text='This filter will narrow results to show only members whose \
        library records are available.')
    sex = FacetChoiceField(label='Gender', widget=CheckboxFieldset(attrs={
        'class': 'choice facet'
    }))
    membership_dates = RangeField(label='Membership Dates', required=False,
        widget=RangeWidget(attrs={'size': 4}))
    birth_year = RangeField(required=False,
        widget=RangeWidget(attrs={'size': 4}))

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

        # if a keyword search term is present, only relevance sort is allowed
        if data and data.get('query', None):
            self.fields['sort'].widget.choices[1] = \
                (self.SORT_CHOICES[1][0], {
                    'label': self.SORT_CHOICES[1][1],
                    'disabled': True})
        # otherwise, relevance is disabled
        else:
            self.fields['sort'].widget.choices[0] = \
                (self.SORT_CHOICES[0][0], {
                    'label': self.SORT_CHOICES[0][1],
                    'disabled': True})
