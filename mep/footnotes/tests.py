from unittest.mock import Mock, patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from mep.footnotes.admin import BibliographyAdmin
from mep.footnotes.models import Bibliography, Footnote, SourceType


class TestSourceType(TestCase):

    def test_item_count(self):
        src_type = SourceType.objects.create(name='website')
        assert src_type.item_count() == 0

        Bibliography.objects.create(bibliographic_note='citation',
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

    def test_image_thumbnail(self):
        fnote = Footnote()
        # no image - returns none, but does not error
        assert not fnote.image_thumbnail()

        # image but no rendering
        with patch.object(Footnote, 'image') as mockimage:
            img = '<img/>'
            mockimage.manifest.extra_data = {}
            mockimage.admin_thumbnail.return_value = img
            assert fnote.image_thumbnail() == img

            test_rendering_url = 'http://img.co/url'
            mockimage.manifest.extra_data = {
                'rendering': {'@id': test_rendering_url}
            }
            image_thumbnail = fnote.image_thumbnail()
            assert img in image_thumbnail
            assert image_thumbnail.startswith(
                '<a target="_blank" href="%s">' % test_rendering_url
            )


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


class TestBibliographyAdmin():

    def test_manifest_thumbnail(self):
        bibadmin = BibliographyAdmin(Mock(), Mock())

        # no manifest, no error
        obj = Mock(manifest=None)
        img = bibadmin.manifest_thumbnail(obj)
        assert not img

        # manifest, no rendering
        obj.manifest = Mock(extra_data={})
        img = '<img/>'
        obj.manifest.admin_thumbnail.return_value = img
        assert bibadmin.manifest_thumbnail(obj) == img

        test_rendering_url = 'http://img.co/url'
        obj.manifest.extra_data = {
            'rendering': {'@id': test_rendering_url}
        }
        manifest_thumbnail = bibadmin.manifest_thumbnail(obj)
        assert img in manifest_thumbnail
        assert manifest_thumbnail.startswith(
            '<a target="_blank" href="%s">' % test_rendering_url
        )
