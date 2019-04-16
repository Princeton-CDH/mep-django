import os
from unittest.mock import Mock, patch

from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from eulxml import xmlmap
import pymarc
import pytest
import requests

from mep.books.oclc import WorldCatClientBase, SRUSearch, SRWResponse

FIXTURES_DIR = os.path.join('mep', 'books', 'fixtures')


class TestWorldCatClientBase:

    def test_init(self):
        with override_settings(OCLC_WSKEY=''):
            with pytest.raises(ImproperlyConfigured):
                WorldCatClientBase()

        with override_settings(OCLC_WSKEY='secretkey'):
            wcb = WorldCatClientBase()
            assert isinstance(wcb.session, requests.Session)
            assert wcb.session.params['wskey'] == 'secretkey'
            assert wcb.query == []

    @override_settings(OCLC_WSKEY='fakekey')
    def test_query_string(self):
        wcb = WorldCatClientBase()
        wcb.query = [
            'A',
            'B',
            'C'
        ]
        assert wcb.query_string == 'A AND B AND C'

    @patch('mep.books.oclc.requests')
    @override_settings(OCLC_WSKEY='fakekey')
    def test_search(self, mock_requests):
        # stub back in codes and exceptions for requests
        mock_requests.codes.ok = requests.codes.ok
        mock_requests.exceptions.ConnectionError = requests.exceptions.ConnectionError
        # mock out an object that can have a return_code to check
        mock_session = mock_requests.Session.return_value
        mock_session.get.return_value = Mock()
        mock_session.get.return_value.status_code = 200
        wcb = WorldCatClientBase()
        wcb.query = ['foo', 'bar']
        # successful run, status code 200
        response = wcb.search(baz='Y', bar='foo')
        # calls get as specified, with passed in kwargs
        mock_session.get.assert_called_with(
            wcb.WORLDCAT_API_BASE,
            params={
                'query': 'foo AND bar',
                'baz': 'Y',
                'bar': 'foo'
            }
        )
        # returns the output of session.get
        assert response == mock_session.get.return_value
        # unsuccessful run, non-200 status code, returns None
        mock_session.get.return_value.status_code = 401
        response = wcb.search()
        assert not response

        # unsuccessful run, raises a requests exception
        # should be handled by returning None
        # make sure that the status_code doesn't affect this
        mock_session.get.return_value.status_code = 200
        mock_session.get.side_effect = requests.exceptions.ConnectionError
        response = wcb.search()
        assert not response


class TestSRUSearch:
    response_fixture = os.path.join(FIXTURES_DIR, 'oclc_srw_response.xml')

    def test_clone(self):
        srus = SRUSearch()
        srus.query = ['foo']
        clone_srus = srus._clone()
        # query lists should be equal but *not* the same object
        assert clone_srus.query == srus.query
        assert clone_srus.query is not srus.query

    def test_filter(self):
        srus = SRUSearch()
        # list of filters as args
        filter_args = ['srw.yr=1901', 'srw.ti exact "Ulysses"']
        filter_srus = srus.filter(*filter_args)
        # args added to list of queries as-is
        assert filter_srus.query == filter_args
        # original query untouched
        assert not srus.query

        # field=value filter with lookup
        title_srus = srus.filter(title="Ulysses")
        # title converted to srw.ti, equal inferred
        assert 'srw.ti=Ulysses' in title_srus.query
        # field__operator=value filter with operator specified
        author_srus = srus.filter(author__any="James Joyce")
        assert 'srw.au any James Joyce' in author_srus.query

    @patch('mep.books.oclc.WorldCatClientBase.search')
    def test_search(self, mock_base_search):
        with open(self.response_fixture) as response:
            # return fixture as response
            mock_base_search.return_value.content = response.read()
            resp = SRUSearch().search()
            # returns response object
            assert isinstance(resp, SRWResponse)

            # no response - no error, no response
            mock_base_search.return_value = None
            assert not SRUSearch().search()


class TestSRWResponse:

    fixture = os.path.join(FIXTURES_DIR, 'oclc_srw_response.xml')

    def get_fixture_obj(self):
        # initialize and return SRWResponse from fixture
        return xmlmap.load_xmlobject_from_file(
            self.fixture, SRWResponse)

    def test_fields(self):
        srw_response = self.get_fixture_obj()
        assert srw_response.num_records == 34154

    def test_marc_records(self):
        srw_response = self.get_fixture_obj()
        marc_records = srw_response.marc_records
        assert len(marc_records) == 10
        assert isinstance(marc_records[0], pymarc.record.Record)

        # sanity check value from first and last record
        assert marc_records[0]['001'].value() == '498910170'
        assert marc_records[-1]['001'].value() == '911727061'
