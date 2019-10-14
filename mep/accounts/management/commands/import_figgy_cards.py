import csv
import os.path
import re

from django.conf import settings
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import models

from djiffy.importer import ManifestImporter
from djiffy.models import IIIFPresentation

from mep.footnotes.models import Bibliography, Footnote


class ManifestImportWithRendering(ManifestImporter):
    '''Extends default importer to capture rendering information,
    if present, in extra data.'''

    def import_manifest(self, manifest, path):
        db_manifest = super().import_manifest(manifest, path)
        # include rendering in extra data
        if hasattr(manifest, 'rendering'):
            db_manifest.extra_data['rendering'] = manifest.rendering
            db_manifest.save()

        return db_manifest


class Command(BaseCommand):
    '''Import IIIF manifests for digitized versions of lending cards
    and associate with card bibliographies and footnotes.'''
    help = __doc__

    #: base url for all card image paths
    pudl_basepath = 'https://diglib.princeton.edu/tools/ib/pudl0123/825298/'
    #: text to use for log entry records
    log_message = 'Migrated from pudl to figgy'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv', help='CSV file mapping PUDL filenames to Figgy canvas IDs')
        parser.add_argument(
            '--update', action='store_true',
            help='Update previously imported manifests')

    def handle(self, *args, **kwargs):
        # Read in the CSV to generate a dictionary lookup of PUDL base
        # filename to figgy file site id, scanned resource id, canvas id

        # first clean up known problems in footnote locations
        self.clean_footnotes()
        # reassociate footnotes linked to the wrong bibliography
        self.clean_orphaned_footnotes()

        card_bibliographies = Bibliography.objects\
            .filter(notes__contains=self.pudl_basepath)

        self.stdout.write('Found %d bibliographies with pudl image paths' %
                          card_bibliographies.count())
        # bail out if there is nothing to do
        if not card_bibliographies.count():
            return

        # initialize manifest importer
        self.importer = ManifestImportWithRendering(
            stdout=self.stdout, stderr=self.stderr, style=self.style,
            update=kwargs['update'])
        # initialize user and content types for creating log entries
        self.script_user = User.objects.get(username=settings.SCRIPT_USERNAME)
        self.bib_ctype = ContentType.objects.get_for_model(Bibliography).pk
        self.footnote_ctype = ContentType.objects.get_for_model(Footnote).pk

        # loop over csv file and get all image paths for each manifest id
        manifest_id = None
        image_paths = []
        canvas_map = {}
        with open(kwargs['csv']) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # if manifest id is set and we hit a new id, process
                # the previous manifest with all gathered paths
                if manifest_id and manifest_id != row['scanned_resource.id']:
                    # update bibliography record
                    # generate manifest URI from canvas id (split on canvas)
                    manifest_uri = list(canvas_map.values())[0]\
                        .partition('/canvas/')[0]
                    # if manifest uri is not set, store it
                    card = self.migrate_card_bibliography(manifest_uri,
                                                          image_paths)
                    # migrate footnotes
                    if card:
                        self.migrate_footnotes(card, canvas_map)

                    # clear out path list and mapping for next manifest
                    image_paths = []
                    canvas_map = {}

                # store current manifest id
                manifest_id = row['scanned_resource.id']
                # add to list of image paths
                # remove .tif extension for simplicity, since some notes
                # have .jpg or .jp2
                image_paths.append(row['pudl filename'].replace('.tif', ''))
                # store mapping from filename to canvas id for updating
                # associated footnotes
                canvas_map[row['pudl filename']] = row['canvas.id']

        # process the last manifest in the file after the loop finishes
        manifest_uri = list(canvas_map.values())[0].partition('/canvas/')[0]
        card = self.migrate_card_bibliography(manifest_uri,
                                              image_paths)
        self.migrate_footnotes(card, canvas_map)

        # report on current states
        pudl_bibliographies = Bibliography.objects \
            .filter(notes__contains=self.pudl_basepath)
        pudl_footnotes = Footnote.objects \
            .filter(location__contains=self.pudl_basepath)

        self.stdout.write('Migration complete.')
        self.stdout.write(
            'Found %d bibliographies and %d footnotes with pudl paths' %
            (pudl_bibliographies.count(), pudl_footnotes.count()))

    def migrate_card_bibliography(self, manifest_uri, image_paths):
        # generate a q filter to find a bibliography record that
        # matches *all* paths
        q_filter = models.Q()
        for path in image_paths:
            q_filter &= models.Q(notes__contains=path)

        cards = Bibliography.objects.filter(q_filter)
        # since some images are used in more than one card, it's
        # possible to find more than one match if we process the shorter
        # image list first
        card = None
        # if we found exactly one card, use it
        if cards.count() == 1:
            card = cards.first()
        # otherwise, find the best match
        if cards.count() > 1:
            # find the best match based on number of images
            for card in cards:
                # if the number of images match, use this card
                if card.notes.count(self.pudl_basepath) == len(image_paths):
                    break
                else:
                    card = None

        if card is None:
            self.stderr.write('Could not identify card for %s' %
                              ','.join(image_paths))
            return

        # if card is found, import the manifest and associate
        iiifpres = IIIFPresentation.from_url(manifest_uri)
        # import the manifest into the database
        db_manifest = self.importer.import_manifest(iiifpres, manifest_uri)
        # associate it with the bibliography and remove the notes
        card.manifest = db_manifest
        # NOTE: assumes notes are *only* image paths.
        # (these were used to generate export for figgy, so this is reasonable)
        card.notes = ''
        card.save()

        # create log entry to document the change
        LogEntry.objects.log_action(
            user_id=self.script_user.id,
            content_type_id=self.bib_ctype,
            object_id=card.pk,
            object_repr=str(card),
            change_message=self.log_message,
            action_flag=CHANGE)

        # return the bibliography object
        return card

    def migrate_footnotes(self, card, canvas_map):
        '''Update footnotes associated with a lending card bibliography.
        Uses footnote location to map from pudl filepath to new
        IIIF canvas. Links to Canvas in the database and also
        stores the canvas id in the location.

        :param card: :class:`~mep.footnotes.models.Bibliography`
        :param canvas_map: dict mapping pudl image paths to corresponding
            canvas id
        '''
        for imgpath, canvas_id in canvas_map.items():
            # search without file extension to match variations
            imgpath_basename = os.path.splitext(imgpath)[0]
            footnotes = card.footnote_set \
                .filter(location__contains=imgpath_basename)
            if footnotes.exists():
                # get the canvas object
                canvas = card.manifest.canvases.get(uri=canvas_id)
                # update all cards at once
                footnote_ids = [fnote.pk for fnote in footnotes]
                footnotes.update(
                    location=canvas_id,
                    image=canvas,
                    bibliography=card
                )
                # get a fresh copy of the footnotes after update
                footnotes = card.footnote_set.filter(id__in=footnote_ids)
                # bulk create log entry records for the updated footnotes
                LogEntry.objects.bulk_create([
                    LogEntry(user_id=self.script_user.id,
                             content_type_id=self.footnote_ctype,
                             object_id=footnote.id,
                             # database limits object repr length
                             object_repr=str(footnote)[:25],
                             change_message=self.log_message,
                             action_flag=CHANGE
                             )
                    for footnote in footnotes
                ])

    # footnote location misspellings to correct in bulk
    location_misspellings = {
        'beinenfeld': 'bienenfeld',  # 49
        'lambirault': 'lamirault',  # 43
        'oerthal': 'oerthel',  # 34
        'Wigram': 'wiggram',  # 10
    }

    def clean_footnotes(self):
        '''Correct known bulk errors in footnotes.'''

        # Fix known bulk errors
        # - misspellings
        for error, correction in self.location_misspellings.items():
            for fnote in Footnote.objects.filter(location__contains=error):
                fnote.location = fnote.location.replace(error, correction)
                fnote.save()
        # special case: dubois footnotes misattributed to dolan in location
        for fnote in Footnote.objects.filter(
                location__contains='dolan',
                bibliography__notes__contains='du_bois'):
            fnote.location = fnote.location.replace('dolan', 'du_bois')
            fnote.save()

        # - 285 double slashes in path (other than for http)
        for fnote in Footnote.objects.filter(location__regex=r'https://.*//'):
            fnote.location = re.sub(r'(?<!https:)//', '/', fnote.location)
            fnote.save()
        # - 147 missing slash between alpha directory and numeric filename
        for fnote in Footnote.objects.filter(location__contains='pudl',
                                             location__regex=r'[a-z]000'):
            fnote.location = re.sub(r'([a-z])(000)', r'\1/\2', fnote.location)
            fnote.save()

        # - filenames with the wrong number of zeros (should have 8 digits)
        for fnote in Footnote.objects.filter(location__contains='pudl') \
                             .filter(location__contains='000') \
                             .exclude(location__regex=r'\/[0-9]{8}\.'):
            # split out file base name, cast as integer, and format properly
            file_basename = os.path.basename(fnote.location)
            number, ext = os.path.splitext(file_basename)
            fnote.location = fnote.location.replace(
                file_basename, '{:08d}{}'.format(int(number), ext))
            fnote.save()

    def clean_orphaned_footnotes(self):
        '''Correct footnotes that are not associated with the correct
        bibliography record.'''

        # find footnote where location does not match list of
        # paths in associated bibliography record
        orphans = Footnote.objects.filter(location__contains='pudl') \
            .exclude(bibliography__notes__contains=models.F('location'))

        for footnote in orphans:
            # use the end of the path to avoid typos in footnotes and
            # bibliography notes that have /tools/ib/ instead of /tools/lib/
            # omit extension to avoid .jp2/jpg variations
            location_path = os.path.splitext(
                footnote.location.partition('/pudl0123/')[-1])[0]
            if location_path in footnote.bibliography.notes:
                continue
            bib = Bibliography.objects \
                .filter(notes__contains=location_path)
            if bib.count() == 1:
                footnote.bibliography = bib.first()
                footnote.save()
            elif bib.count() > 1:
                self.stderr.write(
                    'Found multiple matching bibliography records %s' % bib)
            else:
                self.stderr.write(
                    'No matching bibliography record for %s' % location_path)
