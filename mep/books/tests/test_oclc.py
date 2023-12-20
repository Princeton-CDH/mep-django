from collections import OrderedDict
import os
from unittest.mock import Mock, patch, MagicMock

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from django.test.utils import override_settings
from eulxml import xmlmap
import pymarc
import pytest
import rdflib
import requests

from mep import __version__ as mep_version
from mep.books.oclc import (
    WorldCatClientBase,
    SRUSearch,
    SRWResponse,
    WorldCatEntity,
    SCHEMA_ORG,
)


FIXTURE_DIR = os.path.join("mep", "books", "fixtures")


class TestWorldCatClientBase:
    def test_init(self):
        with override_settings(OCLC_WSKEY=""):
            with pytest.raises(ImproperlyConfigured):
                WorldCatClientBase()

        with override_settings(OCLC_WSKEY="secretkey", TECHNICAL_CONTACT=None):
            wcb = WorldCatClientBase()
            assert isinstance(wcb.session, requests.Session)
            assert wcb.wskey == "secretkey"

            # sets user agent with versions
            assert "User-Agent" in wcb.session.headers
            assert "mep-django/%s" % mep_version in wcb.session.headers["User-Agent"]
            assert (
                "(python-requests/%s)" % requests.__version__
                in wcb.session.headers["User-Agent"]
            )

            # no From header if no technical contact
            assert "From" not in wcb.session.headers

            with override_settings(TECHNICAL_CONTACT="dev@example.com"):
                wcb = WorldCatClientBase()
                assert "From" in wcb.session.headers
                assert wcb.session.headers["From"] == "dev@example.com"

    @patch("mep.books.oclc.requests", **{"__version__": requests.__version__})
    @override_settings(OCLC_WSKEY="fakekey")
    def test_search(self, mock_requests):
        # stub back in codes and exceptions for requests
        mock_requests.codes = requests.codes
        mock_requests.exceptions = requests.exceptions
        # mock_requests.__version__ == requests.__version__
        # mock out an object that can have a return_code to check
        mock_session = mock_requests.Session.return_value
        mock_session.get.return_value = Mock()
        mock_session.get.return_value.status_code = 200
        wcb = WorldCatClientBase()
        # successful run, status code 200
        response = wcb.search(query="foo AND bar", baz="Y", bar="foo")
        # calls get as specified, with passed in kwargs
        mock_session.get.assert_called_with(
            wcb.WORLDCAT_API_BASE,
            params={
                "query": "foo AND bar",
                "baz": "Y",
                "bar": "foo",
                "wskey": settings.OCLC_WSKEY,
            },
        )
        # returns the output of session.get
        assert response == mock_session.get.return_value
        # unsuccessful run, non-200 status code, returns None
        mock_session.get.return_value.status_code = 401
        response = wcb.search(query="foo")
        assert not response

        # unsuccessful run, raises a requests exception
        # should be handled by returning None
        # make sure that the status_code doesn't affect this
        mock_session.get.return_value.status_code = 200
        mock_session.get.side_effect = requests.exceptions.ConnectionError
        response = wcb.search()
        assert not response


SRW_RESPONSE_FIXTURE = os.path.join(FIXTURE_DIR, "oclc_srw_response.xml")


def get_srwresponse_xml_fixture():
    # test utility method to initialize and return SRWResponse
    # XmlObject from fixture
    return xmlmap.load_xmlobject_from_file(SRW_RESPONSE_FIXTURE, SRWResponse)


@override_settings(OCLC_WSKEY="my-secret-key")
class TestSRUSearch(SimpleTestCase):
    def test_lookup_to_search(self):
        # list of filters as args
        search_args = ["srw.yr=1901", 'srw.ti exact "Ulysses"']
        search_query = SRUSearch._lookup_to_search(*search_args)
        assert search_query == " AND ".join(search_args)

        # field=value filter with lookup
        # - title converted to srw.ti, equal inferred
        assert SRUSearch._lookup_to_search(title="Ulysses") == 'srw.ti="Ulysses"'
        # field__operator=value filter with operator specified
        assert (
            SRUSearch._lookup_to_search(author__any="James Joyce")
            == 'srw.au any "James Joyce"'
        )
        # numeric doesn't get quoted
        assert SRUSearch._lookup_to_search(year=1950) == "srw.yr=1950"

        # NOT option instead of AND
        query_string = SRUSearch._lookup_to_search(
            title="Ulysses", material_type__notexact="Internet Resource"
        )
        # can't test directly because order is not guaranteed in py3.5
        assert 'srw.ti="Ulysses"' in query_string
        assert 'NOT srw.mt exact "Internet Resource"' in query_string
        assert "AND NOT" not in query_string

    @patch("mep.books.oclc.WorldCatClientBase.search")
    def test_search(self, mock_base_search):
        with open(SRW_RESPONSE_FIXTURE) as response:
            # return fixture as response
            mock_base_search.return_value.content = response.read()
            resp = SRUSearch().search()
            # returns response object
            assert isinstance(resp, SRWResponse)

            # 200 response but not valid xml
            mock_base_search.return_value.content = "foo"
            # use patch since can't get pytest caplog to work
            with patch("mep.books.oclc.logger") as mock_logger:
                assert not SRUSearch().search()
                assert mock_logger.error.call_count == 1
                args = mock_logger.error.call_args[0]
                assert "Error parsing response" in args[0]

            # no response - no error, no response
            mock_base_search.return_value = None
            assert not SRUSearch().search()

    @override_settings(OCLC_WSKEY="secretkey", TECHNICAL_CONTACT="foo@example.com")
    @patch("mep.books.oclc.WorldCatEntity", spec=True)
    def test_get_worldcat_rdf(self, mock_worldcatentity):
        marc_record = get_srwresponse_xml_fixture().marc_records[0]
        sru_search = SRUSearch()
        wc_rdf = sru_search.get_worldcat_rdf(marc_record)
        mock_worldcatentity.assert_called_with(marc_record, sru_search.session)
        assert isinstance(wc_rdf, WorldCatEntity)


class TestSRWResponse:
    def test_fields(self):
        srw_response = get_srwresponse_xml_fixture()
        assert srw_response.num_records == 34154

    def test_marc_records(self):
        srw_response = get_srwresponse_xml_fixture()
        marc_records = srw_response.marc_records
        assert len(marc_records) == 10
        assert isinstance(marc_records[0], pymarc.record.Record)

        # sanity check value from first and last record
        assert marc_records[0]["001"].value() == "498910170"
        assert marc_records[-1]["001"].value() == "911727061"


class TestWorldCatEntity:
    def worldcat_entity_from_fixture(self):
        """initialize worldcat entity from fixture data"""
        marc_record = get_srwresponse_xml_fixture().marc_records[0]
        # load fixture as graph and set mock to return it.
        # fixture *must* match id in the marc record
        test_graph = rdflib.Graph()
        test_graph.parse(os.path.join(FIXTURE_DIR, "oclc.rdf"))

        mock_session = Mock()
        with patch.object(WorldCatEntity, "get_oclc_rdf") as mock_get_oclc_rdf:
            mock_get_oclc_rdf.return_value = test_graph
            return WorldCatEntity(marc_record, mock_session)

    def worldcat_entity_from_fixture_timetide(self):
        """initialize worldcat entity from fixture data for time & tide"""
        marc_record = MagicMock()
        marc_record["001"].value.return_value = "3484871"

        # load fixture as graph and set mock to return it.
        # fixture *must* match id in the marc record
        test_graph = rdflib.Graph()
        test_graph.parse(os.path.join(FIXTURE_DIR, "oclc_3484871.rdf"))

        mock_session = Mock()
        with patch.object(WorldCatEntity, "get_oclc_rdf") as mock_get_oclc_rdf:
            mock_get_oclc_rdf.return_value = test_graph
            return WorldCatEntity(marc_record, mock_session)

    def test_str(self):
        wc_entity = self.worldcat_entity_from_fixture()
        assert str(wc_entity) == wc_entity.item_uri

    def test_repr(self):
        wc_entity = self.worldcat_entity_from_fixture()
        assert repr(wc_entity) == "<WorldCatEntity %s>" % wc_entity.item_uri

    def test_oclc_uri(self):
        # use first marc record from response fixture
        marc_record = get_srwresponse_xml_fixture().marc_records[0]
        assert (
            WorldCatEntity.oclc_uri(marc_record)
            == "http://www.worldcat.org/oclc/%s" % marc_record["001"].value()
        )

    def test_init(self):
        marc_record = get_srwresponse_xml_fixture().marc_records[0]
        # load fixture as graph and set mock to return it.
        # fixture *must* match id in the marc record
        test_graph = rdflib.Graph()
        test_graph.parse(os.path.join(FIXTURE_DIR, "oclc.rdf"))

        wc_entity = self.worldcat_entity_from_fixture()
        assert wc_entity.marc_record["001"].value() == marc_record["001"].value()
        assert wc_entity.session
        assert wc_entity.item_uri == WorldCatEntity.oclc_uri(marc_record)
        assert isinstance(wc_entity.rdf_resource, rdflib.resource.Resource)

        # simulate graph load failure
        with patch.object(WorldCatEntity, "get_oclc_rdf") as mock_get_oclc_rdf:
            marc_record = MagicMock()
            marc_record["001"].value.return_value = "3484871"
            mock_get_oclc_rdf.return_value = None
            with pytest.raises(ConnectionError):
                WorldCatEntity(marc_record, Mock())

    @patch("mep.books.oclc.rdflib", spec=True)
    def test_get_oclc_rdf(self, mockrdflib):
        # stub back in codes and exceptions for requests
        mock_session = Mock()
        mock_session.codes = requests.codes
        mock_session.exceptions = requests.exceptions

        # load fixture as graph and set mock to return it.
        # fixture *must* match id in the marc record
        test_graph = rdflib.Graph()
        test_graph.parse(os.path.join(FIXTURE_DIR, "oclc.rdf"))

        # have to patch at rdflib level because of the way it is imported
        mockrdflib.Graph.return_value = test_graph
        # use the real URIRef
        mockrdflib.URIRef = rdflib.URIRef

        marc_record = get_srwresponse_xml_fixture().marc_records[0]

        with patch.object(test_graph, "parse") as mockparse:
            # simulate success
            mock_response = mock_session.get.return_value
            mock_response.status_code = requests.codes.ok

            wc_entity = WorldCatEntity(marc_record, mock_session)
            mockrdflib.Graph.assert_called_with()
            mock_session.get.assert_called_with(
                "http://www.worldcat.org/oclc/%s.rdf" % marc_record["001"].value()
            )
            mockparse.assert_called_with(data=mock_response.content.decode())
            assert wc_entity.rdf_resource._graph == test_graph

            # simulate failure on request

            # can't figure out how to use pytest caplog fixture,
            # so using patch instead
            with patch("mep.books.oclc.logger") as mock_logger:
                mock_response.status_code = requests.codes.not_found
                wc_entity = None
                with pytest.raises(ConnectionError):
                    wc_entity = WorldCatEntity(marc_record, mock_session)
                # entity not initialized
                assert not wc_entity
                # should not error, return none, and log the error
                mock_logger.error.assert_called_with(
                    "Error loading OCLC record as RDF %s => %d",
                    WorldCatEntity.oclc_uri(marc_record),
                    mock_response.status_code,
                )

    def test_work_uri(self):
        wc_entity = self.worldcat_entity_from_fixture()
        assert wc_entity.work_uri == "http://worldcat.org/entity/work/id/5090374654"
        # handle missing work uri
        wc_entity.rdf_resource._graph = rdflib.Graph()
        assert wc_entity.work_uri is None

    def test_item_type(self):
        wc_entity = self.worldcat_entity_from_fixture()
        # how to ensure we get the most specific type?
        assert wc_entity.item_type == "http://schema.org/Book"

        time_and_tide = self.worldcat_entity_from_fixture_timetide()
        assert time_and_tide.item_type == "http://schema.org/Periodical"

        # simulate article result
        wc_entity.rdf_resource.remove(rdflib.RDF.type)
        wc_entity.rdf_resource.add(rdflib.RDF.type, SCHEMA_ORG.Article)
        assert wc_entity.item_type == "http://schema.org/Article"

        # simulate no type
        wc_entity.rdf_resource.remove(rdflib.RDF.type)
        assert wc_entity.item_type is None

    def test_genres(self):
        time_and_tide = self.worldcat_entity_from_fixture_timetide()
        # use set to check values without failing on order
        assert set(time_and_tide.genres) == set(["Periodicals", "Electronic Books"])

        # other fixture has no genre
        wc_entity = self.worldcat_entity_from_fixture()
        assert wc_entity.genres == []

    def test_subjects(self):
        time_and_tide = self.worldcat_entity_from_fixture_timetide()
        subjects = time_and_tide.subjects
        # expect five from fixture; excludes experimental worldcat URIs
        assert len(subjects) == 5
        assert "http://id.worldcat.org/fast/1259831" in subjects
        assert "http://viaf.org/viaf/151712903" in subjects
        assert (
            "http://experiment.worldcat.org/entity/work/data/3372107206#Organization/"
            not in subjects
        )

        # other fixture has only one experimental subject
        wc_entity = self.worldcat_entity_from_fixture()
        assert wc_entity.subjects == []
