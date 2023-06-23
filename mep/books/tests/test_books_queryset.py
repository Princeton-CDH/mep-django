from unittest.mock import patch

from mep.books.queryset import WorkSolrQuerySet


class TestWorkSolrQuerySet:
    def test_search_admin_work(self):
        wqs = WorkSolrQuerySet()
        with patch.object(wqs, "search") as mocksearch:
            wqs.search_admin_work("english novel")
            mocksearch.assert_called_with(wqs.admin_work_qf)
            mocksearch.return_value.raw_query_parameters.assert_called_with(
                work_query="english novel"
            )
