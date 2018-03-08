from django import forms
from django.template.loader import get_template

from mep.people.models import Person


class PersonChoiceField(forms.ModelChoiceField):
    label_template = get_template('people/snippets/person_option_label.html')

    def label_from_instance(self, person):
        return self.label_template.render({'person': person})


class PersonMergeForm(forms.Form):
    primary_person = PersonChoiceField(label='Primary record', queryset=None,
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

