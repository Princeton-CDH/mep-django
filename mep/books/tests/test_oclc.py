import os
from unittest.mock import Mock, patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from django.test.utils import override_settings
import pytest
import requests

from mep.books.oclc import WorldCatClientBase

FIXTURES_DIR = os.path.join('mep', 'books', 'fixtures')

class TestWorldCatClientBase(SimpleTestCase):

    def test_init(self):
        with self.settings(OCLC_WSKEY=''):
            with pytest.raises(ImproperlyConfigured):
                wc = WorldCatClientBase()
        with self.settings(OCLC_WSKEY='secretkey'):
            wc = WorldCatClientBase()
            assert isinstance(wc.session, requests.Session)
            assert wc.session.params['wskey'] == 'secretkey'
            assert wc.query == []

    @override_settings(OCLC_WSKEY='fakekey')
    def test_query_string(self):
        wc = WorldCatClientBase()
        wc.query = [
            'A',
            'B',
            'C'
        ]
        assert wc.query_string == 'A AND B AND C'

    @patch('mep.books.oclc.requests')
    @override_settings(OCLC_WSKEY='fakekey')
    def test_search(self, mock_requests):
        mock_requests.codes.OK = request.codes.OK
        mock_session = mock_requests.Session.return_value
        mock_session.get.return_value = Mock()
        mock_session.get.return_value.status_code = 200
        wc = WorldCatClientBase()
        wc.query = ['foo', 'bar']
        # successful run, status code 200
        response = wc.search(baz='Y',bar='foo')
        # calls get as specified, with passed in kwargs
        mock_session.get.assert_called_with(
            wc.WORLDCAT_API_BASE,
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
        response = wc.search()
        assert response is None
        # unsuccessful run, raises a requests exception
        # should be handled by returning None
        # make sure that the status_code doesn't affect this
        mock_session.get.return_value.status_code = 200
        mock_session.get.side_effect = requests.ConnectionError
        response = wc.search()
        assert response is None