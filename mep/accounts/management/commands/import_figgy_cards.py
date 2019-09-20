import csv
from os.path import splitext


from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from djiffy.models import IIIFPresentation
from djiffy.importer import ManifestImporter

from mep.footnotes.models import Bibliography, Footnote


class Command(BaseCommand):
    '''Import IIIF manifests for digitized versions of lending cards
    and associate with card bibliographies and footnotes.'''
    help = __doc__

    pudl_basepath = 'https://diglib.princeton.edu/tools/ib/pudl0123/825298/'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv', help='CSV file mapping PUDL filenames to Figgy canvas IDs')
        parser.add_argument(
            '--update', action='store_true',
            help='Update previously imported manifests')

    def handle(self, *args, **kwargs):
        # Read in the CSV to generate a dictionary lookup of PUDL base
        # filename to figgy file site id, scanned resource id, canvas id


        # loop over csv file
        # get groups of paths for each manifest id
        # find matching bibliography with all paths
        # - if no match, error!
        # update bibliography
        # update associated footnotes

        mapping = {}
        with open(kwargs['csv']) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row['pudl filename']
                mapping[row['pudl filename']] = row

        card_bibliographies = Bibliography.objects\
            .filter(notes__contains=self.pudl_basepath)

        self.stdout.write('Found %d bibliographies with pudl image path' %
                          card_bibliographies.count())
        # TODO: bail if nothing to do

        importer = ManifestImporter(stdout=self.stdout, stderr=self.stderr,
                                    style=self.style, update=kwargs['update'])

        self.script_user = User.objects.get(username=settings.SCRIPT_USERNAME)
        self.bib_ctype = ContentType.objects.get_for_model(Bibliography).pk
        self.footnote_ctype = ContentType.objects.get_for_model(Footnote).pk

        for card in card_bibliographies:
            # TODO convert into method ?
            image_paths = [
                path.partition(self.pudl_basepath)[2].strip()
                    .replace('.jp2', '.tif').replace('.jpg', '.tif').lstrip('/')
                for path in card.notes.split('\n')
                if self.pudl_basepath in path
            ]

            manifest_uri = None
            for img in image_paths:

                # print(img)
                # print(mapping[img]['scanned_resource.id'])
                # get manifest uri for this canvas
                img_manifest = mapping[img]['canvas.id'].partition('/canvas/')[0]
                # if manifest uri is not set, store it
                if manifest_uri is None:
                    manifest_uri = img_manifest
                # if it is already set, make sure we have the same one
                elif manifest_uri != img_manifest:
                    self.stdout.write('Manifest error!')
                    continue

            iiifpres = IIIFPresentation.from_url(manifest_uri)
            # import the manifest into the database
            db_manifest = importer.import_manifest(iiifpres, manifest_uri)
            print(db_manifest)
            # associate it with the bibliography and remove the notes
            card.manifest = db_manifest
            # NOTE: assumes notes are *only* image paths.
            # (used to generate export for figgy, so should be reasonable)
            card.notes = ''
            card.save()

            # TODO: fix footnotes
            # TODO: django history

            # for each image, find and update all footnotes with that path
            print(card)
            for img in image_paths:
                print(img)
                # search on the image path without the extension, since
                # csv uses .tif but many pudl urls are .jp2
                imgpath = splitext(img)[0]
                print(imgpath)
                canvas_id = mapping[img]['canvas.id']

                fn_count = card.footnote_set.filter(location__contains=imgpath).count()
                if fn_count:
                    print(manifest_uri)
                    print('%d footnotes' % fn_count)
                    print(canvas_id)
                # skip if no footnotes to update
                else:
                    continue

                canvas = db_manifest.canvases.get(uri=canvas_id)
                card.footnote_set.filter(location__contains=imgpath) \
                    .update(
                        location=canvas_id,
                        image=canvas,
                        bibliography=card
                )


                # TODO: edit goodwin footnote to remove tif 0004 ? (actually enfield()


                # footnotes = Footnote.objects.filter(location__contains=img)
                # for footnote in footnotes:
                #     # convert location note o new canvas id
                #     footnote.location = canvas_id
                #     # associate canvas
                #     footnote.image_location = canvas
                #     # make sure footnote is associated with current card bibliography
                #     footnote.bibliography = card
                #     # save footnote
                #     footnote.save()

        # self.summarize(dmi.stats)
