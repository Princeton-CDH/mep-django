from django import forms
from django.template.loader import get_template

from mep.common.forms import (
    CheckboxFieldset,
    ChoiceLabel,
    FacetChoiceField,
    FacetForm,
    RangeField,
    RangeForm,
    RangeWidget,
    SelectWithDisabled,
)
from mep.people.models import Person


class PersonChoiceField(forms.ModelChoiceField):
    label_template = get_template("people/snippets/person_option_label.html")

    def label_from_instance(self, person):
        return self.label_template.render({"person": person})


class PersonMergeForm(forms.Form):
    primary_person = PersonChoiceField(
        label="Primary record",
        queryset=None,
        help_text="Select the person record to preserve. "
        + "All events from other people will be reassociated with "
        + "their account.",
        empty_label=None,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        person_ids = kwargs.get("person_ids", [])
        try:
            del kwargs["person_ids"]
        except KeyError:
            pass

        super().__init__(*args, **kwargs)
        self.fields["primary_person"].queryset = Person.objects.filter(
            id__in=person_ids
        )


class MemberSearchForm(RangeForm, FacetForm):
    """Member search form"""

    SORT_CHOICES = [
        ("relevance", "Relevance"),
        ("name", "Name A – Z"),
    ]

    # NOTE these are not set by default!
    error_css_class = "error"
    required_css_class = "required"

    query = forms.CharField(
        label="Keyword or Phrase",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Search member", "aria-label": "Keyword or Phrase"}
        ),
    )
    sort = forms.ChoiceField(
        choices=SORT_CHOICES, required=False, widget=SelectWithDisabled
    )
    has_card = forms.BooleanField(
        label="Card",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"aria-label": "Card", "aria-describedby": "has_card_tip"}
        ),
        help_text="Limit to members with lending library cards.",
    )
    gender = FacetChoiceField(
        label="Gender",
        none_val="Unidentified",
        widget=CheckboxFieldset(
            attrs={"class": "choice facet", "aria-describedby": "gender_tip"}
        ),
        help_text="Click to learn more about gender representation in the Project.",
    )
    membership_dates = RangeField(
        label="Membership Years", required=False, widget=RangeWidget(attrs={"size": 4})
    )
    birth_year = RangeField(
        label="Birth Year", required=False, widget=RangeWidget(attrs={"size": 4})
    )
    nationality = FacetChoiceField(
        label="Nationality",
        hide_threshold=0,
        none_val="Unidentified",
        widget=CheckboxFieldset(
            attrs={"class": "text facet", "aria-describedby": "nationality-info"}
        ),
    )
    arrondissement = FacetChoiceField(
        label="Arrondissement",
        hide_threshold=0,
        widget=CheckboxFieldset(attrs={"class": "text facet"}),
    )

    def __init__(self, data=None, *args, **kwargs):
        """
        Override to set choices dynamically based on form kwargs.
        """
        super().__init__(data=data, *args, **kwargs)

        # if a keyword search term is present, only relevance sort is allowed
        if data and data.get("query", None):
            self.fields["sort"].widget.choices[1] = (
                self.SORT_CHOICES[1][0],
                ChoiceLabel(self.SORT_CHOICES[1][1], disabled=True),
            )
        # otherwise, relevance is disabled
        else:
            self.fields["sort"].widget.choices[0] = (
                self.SORT_CHOICES[0][0],
                ChoiceLabel(self.SORT_CHOICES[0][1], disabled=True),
            )
