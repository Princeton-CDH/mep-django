from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from .models import SourceType, Bibliography, Footnote


class TestSourceType(TestCase):

    def test_item_count(self):
        src_type = SourceType.objects.create(name='website')
        assert src_type.item_count() == 0

        bibl = Bibliography.objects.create(bibliographic_note='citation',
            source_type=src_type)
        assert src_type.item_count() == 1


class TestBibliography(TestCase):

    def test_str(self):
        src_type = SourceType.objects.create(name='website')
        bibl = Bibliography.objects.create(bibliographic_note='citation',
            source_type=src_type)
        assert str(bibl) == 'citation'

    def test_footnote_count(self):
        src_type = SourceType.objects.create(name='website')
        bibl = Bibliography.objects.create(bibliographic_note='citation',
            source_type=src_type)
        assert bibl.footnote_count() == 0

        # find an arbitrary content type to attach a footnote to
        content_type = ContentType.objects.first()
        Footnote.objects.create(bibliography=bibl, content_type=content_type,
            object_id=1, is_agree=False)
        assert bibl.footnote_count() == 1

class TestFootnote(TestCase):

    def test_str(self):
        src_type = SourceType.objects.create(name='website')
        bibl = Bibliography.objects.create(bibliographic_note='citation',
            source_type=src_type)
        # find an arbitrary content type to attach a footnote to
        content_type = ContentType.objects.first()
        fn = Footnote.objects.create(bibliography=bibl, content_type=content_type,
            object_id=1, is_agree=False)


        assert 'Footnote on %s' % fn.content_object in str(fn)

        assert '(%s)' % bibl in str(fn)
        fn.location = 'http://so.me/url/'
        assert '(%s %s)' % (bibl, fn.location) in str(fn)


class TestBibliographyAutocomplete(TestCase):

    def test_bibliography_autocomplete(self):

        url = reverse('footnotes:bibliography-autocomplete')
        res = self.client.get(url)

        # getting the view returns 200
        assert res.status_code == 200
        data = res.json()
        # there is a results list in the JSON
        assert 'results' in data
        # it is empty because there are no accounts or query
        assert not data['results']

        # - test search and sort
        source_type = SourceType.objects.create(name='card')
        bib1 = Bibliography.objects.create(
            source_type=source_type,
            bibliographic_note='Found in a box with some foobars.'
        )
        bib2 = Bibliography.objects.create(
            source_type=source_type,
            bibliographic_note='The private collection of Mr. Baz'
        )
        # return all
        res = self.client.get(url)
        data = res.json()
        assert res.status_code == 200
        assert 'results' in data
        assert len(data['results']) == 2
        assert data['results'][0]['text'] == str(bib1)

        # return one based on search
        data = self.client.get(url, {'q': 'baz'}).json()
        assert res.status_code == 200
        assert 'results' in data
        assert len(data['results']) == 1
        assert data['results'][0]['text'] == str(bib2)

