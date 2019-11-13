from datetime import date
from unittest.mock import Mock, patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from djiffy.models import Manifest

from mep.accounts.models import Account, Event
from mep.footnotes.admin import BibliographyAdmin
from mep.footnotes.models import Bibliography, Footnote, SourceType
from mep.people.models import Person


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

    def test_items_to_index(self):
        with patch.object(Bibliography.objects, 'filter') as \
                mock_bib_filter:
            Bibliography.items_to_index()
            mock_bib_filter.assert_called_with(account__isnull=False,
                                               manifest__isnull=False)

    def test_index_data(self):
        src_type = SourceType.objects.create(name='Lending Library Card')
        bibl = Bibliography.objects.create(bibliographic_note='citation',
                                           source_type=src_type)
        # no account or manifest, no index data
        index_data = bibl.index_data()
        assert 'item_type' not in index_data
        assert len(index_data.keys()) == 1
        # account but no manifest, no index data
        acct = Account.objects.create(card=bibl)
        assert 'item_type' not in bibl.index_data()

        bibl.manifest = Manifest()
        with patch.object(Manifest, 'thumbnail') as mock_thumbnail:
            test_iiif_img_url = 'iiif.image.url'
            mock_thumbnail.image.size.return_value = test_iiif_img_url
            index_data = bibl.index_data()
            assert index_data['thumbnail_t'] == test_iiif_img_url
            assert index_data['thumbnail2x_t'] == test_iiif_img_url
            mock_thumbnail.image.size.assert_any_call(width=225)
            mock_thumbnail.image.size.assert_any_call(width=225 * 2)

            # add people and events to account
            leon = Person.objects.create(sort_name='Edel, Leon', slug='edel-l')
            bertha = Person.objects.create(sort_name='Edel, Bertha',
                                           slug='edel-b')
            acct.persons.add(leon)
            acct.persons.add(bertha)
            Event.objects.create(account=acct, start_date=date(1919, 11, 17))
            Event.objects.create(account=acct, start_date=date(1922, 1, 15))
            Event.objects.create(account=acct, start_date=date(1936, 5, 3))
            index_data = bibl.index_data()

            assert leon.sort_name in index_data['cardholder_t']
            assert bertha.sort_name in index_data['cardholder_t']
            assert index_data['cardholder_sort_s'] == bertha.sort_name
            for year in (1919, 1922, 1936):
                assert year in index_data['years_is']
            assert index_data['start_i'] == 1919
            assert index_data['end_i'] == 1936


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


class TestBibliographyAdmin:

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
