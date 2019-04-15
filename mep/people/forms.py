from django import forms
from django.template.loader import get_template

from mep.people.models import Person


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


class MemberSearchForm(forms.Form):
    '''Member search form'''

    SORT_CHOICES = [
        ('relevance', 'Relevance'),
        ('name', 'Name A-Z'),
    ]

    query = forms.CharField(label='Keyword or Phrase', required=False,
                            widget=forms.TextInput(attrs={
                                'placeholder': 'Search member',
                                'aria-label': 'Keyword or Phrase'
                            }))
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False,
                             widget=SelectWithDisabled)
    has_card = forms.BooleanField(label='Card', required=False,
        widget=forms.CheckboxInput(attrs={
            'aria-label': 'Card',
            'aria-describedby': 'has_card_tip'
        }),
        help_text='This filter will narrow results to show only members whose \
        library records are available.')

    def __init__(self, data=None, *args, **kwargs):
        '''
        Set choices dynamically based on form kwargs and presence of keywords.
        '''
        super().__init__(data=data, *args, **kwargs)


        # relevance is disabled unless we have a keyword query present
        if not data or not 'query' in data or not data['query']:
            self.fields['sort'].widget.choices[0] = \
                ('relevance', {'label': 'Relevance', 'disabled': True})
