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

    range_field_map = {
        'membership_dates': 'account_years',
    }

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

    def set_daterange_placeholders(self, min_max_conf):
        '''Set the min, max, and placeholder values for all fields associated
        with :class:`mep.common.forms.RangeWidget`'''
        for field, field_obj in self.fields.items():
            if isinstance(field_obj, RangeField):
                stats_field_name = self.range_field_map.get(field, field)
                min_year, max_year = min_max_conf[stats_field_name]
                start_widget, end_widget = field_obj.widget.widgets

                # set placeholders for widgets individually
                start_widget.attrs['placeholder'] = min_year
                end_widget.attrs['placeholder'] = max_year
                # valid min and max for both via multiwidget
                field_obj.widget.attrs.update({
                    'min': min_year,
                    'max': max_year
                })

    def __init__(self, data=None, *args, **kwargs):
        '''
        Set choices dynamically based on form kwargs and presence of keywords.
        '''
        super().__init__(data=data, *args, **kwargs)

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
