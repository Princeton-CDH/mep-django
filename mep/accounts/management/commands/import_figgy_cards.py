import csv

from django.conf import settings
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import models

from djiffy.importer import ManifestImporter
from djiffy.models import IIIFPresentation

from mep.footnotes.models import Bibliography, Footnote


class Command(BaseCommand):
    '''Import IIIF manifests for digitized versions of lending cards
    and associate with card bibliographies and footnotes.'''
    help = __doc__

    pudl_basepath = 'https://diglib.princeton.edu/tools/ib/pudl0123/825298/'
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

        card_bibliographies = Bibliography.objects\
            .filter(notes__contains=self.pudl_basepath)

        self.stdout.write('Found %d bibliographies with pudl image paths' %
                          card_bibliographies.count())
        # bail out if there is nothing to do
        if not card_bibliographies.count():
            return

        # initialize manifest importer
        self.importer = ManifestImporter(
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

        # TODO: clean up abandoned footnotes (?)

        # summarize what was done

        # self.summarize(dmi.stats)

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
            object_repr=repr(card),
            change_message=self.log_message,
            action_flag=CHANGE)

        # return the bibliography object
        return card

    def migrate_footnotes(self, card, canvas_map):
        for imgpath, canvas_id in canvas_map.items():
            footnotes = card.footnote_set.filter(location__contains=imgpath)
            if footnotes.exists():
                # get the canvas object
                canvas = card.manifest.canvases.get(uri=canvas_id)
                # update all cards at once
                footnotes.update(
                    location=canvas_id,
                    image=canvas,
                    bibliography=card
                )
                # bulk create log entry records for the updated footnotes
                LogEntry.objects.bulk_create([
                    LogEntry(user_id=self.script_user.id,
                             content_type_id=self.footnote_ctype,
                             object_id=footnote.id,
                             object_repr=repr(footnote),
                             change_message=self.log_message,
                             action_flag=CHANGE
                             )
                    for footnote in footnotes
                ])
