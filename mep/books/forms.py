from django import forms

from mep.common.forms import (
    ChoiceFieldWithDisabled,
    FacetForm,
    RangeField,
    RangeForm,
    RangeWidget,
    SelectWithDisabled,
)


class WorkSearchForm(RangeForm, FacetForm):
    """Book search form"""

    SORT_CHOICES = [
        ("title", "Title A – Z"),
        ("author", "Author A – Z"),
        ("pubdate", "Publication Date (Newest – Oldest)"),
        ("circulation_date", "Circulation Date (Oldest – Newest)"),
        ("circulation", "Circulation (Highest – Lowest)"),
        ("relevance", "Relevance"),
    ]

    # NOTE these are not set by default!
    error_css_class = "error"
    required_css_class = "required"

    query = forms.CharField(
        label="Keyword or Phrase",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search by title, author, or keyword",
                "aria-label": "Keyword or Phrase",
            }
        ),
    )
    sort = ChoiceFieldWithDisabled(
        choices=SORT_CHOICES, required=False, widget=SelectWithDisabled
    )
    circulation_dates = RangeField(
        label="Circulation Years", required=False, widget=RangeWidget(attrs={"size": 4})
    )

    def __init__(self, data=None, *args, **kwargs):
        """
        Override to disable relevance sort when there are no keyword
        search terms active.
        """
        super().__init__(data=data, *args, **kwargs)

        # if a keyword search term is not present, disable relevance sort
        if data and not data.get("query", None):
            self.fields["sort"].widget.choices[-1] = (
                self.SORT_CHOICES[-1][0],
                {"label": self.SORT_CHOICES[-1][1], "disabled": True},
            )
