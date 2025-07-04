from django.test import TestCase

from mep.books.forms import WorkSearchForm
from mep.common.forms import ChoiceLabel


class TestWorkSearchForm(TestCase):
    def test_init(self):
        data = {"query": "Hemingway", "sort": "title"}
        # -1 index because relevance is currently last in the options

        # has query, relevance enabled (unchanged from config)
        form = WorkSearchForm(data)
        assert form.fields["sort"].widget.choices[-1] == form.SORT_CHOICES[-1]

        # empty query, relevance disabled
        data["query"] = ""
        form = WorkSearchForm(data)
        assert form.fields["sort"].widget.choices[-1][0] == "relevance"
        label = form.fields["sort"].widget.choices[-1][1]
        assert isinstance(label, ChoiceLabel)
        assert label.label == "Relevance"
        assert label.disabled == True

        # no query but some data; relevance still disabled
        del data["query"]
        form = WorkSearchForm(data)
        assert form.fields["sort"].widget.choices[-1][0] == "relevance"
        label = form.fields["sort"].widget.choices[-1][1]
        assert isinstance(label, ChoiceLabel)
        assert label.label == "Relevance"
        assert label.disabled == True
