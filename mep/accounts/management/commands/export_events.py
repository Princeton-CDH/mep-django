'''
Manage command to export event data for use by others.

Generates a CSV and JSON file including details on every event in the
database with summary details and URIs for associated library member(s)
and book (for events linked to books).

Takes an optional argument to specify the output directory. Otherwise,
files are created in the current directory.

'''

import codecs
import csv
import json
import os.path
from collections import OrderedDict

from django.core.management.base import BaseCommand
import progressbar

from mep.accounts.models import Event
from mep.common.utils import absolutize_url


class Command(BaseCommand):
    '''Export event data'''
    help = __doc__

    #: fields for CSV output
    csv_fields = [
        'event type',
        'start date', 'end date',
        'member sort names', 'member names', 'member URIs',
        # subscription specific
        'subscription price paid', 'subscription deposit',
        'subscription duration', 'subscription duration days',
        'subscription volumes', 'subscription category',
        # reimbursement specific
        'reimbursement refund',
        # borrow specific
        'borrow status',
        # purchase specific
        'purchase price',
        # related book/item
        'item title',  # work URI TBD
        'item work uri', 'item edition uri', 'item notes',
        # generic
        'notes',
        # footnote/citation
        'source citation', 'source manifest', 'source image'
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '-d', '--directory',
            help='Specify the directory where files should be generated')

    def handle(self, *args, **kwargs):

        base_filename = 'events'
        if kwargs['directory']:
            base_filename = os.path.join(kwargs['directory'], base_filename)

        # generate filenames based on slug ?
        # Can we use the same data to generate both CSV and JSON?
        data = self.get_data()
        self.stdout.write('Exporting JSON')
        # list of dictionaries can be output as is for JSON export
        with open('{}.json'.format(base_filename), 'w') as jsonfile:
            for chunk in json.JSONEncoder(indent=2).iterencode(data):
                jsonfile.write(chunk)

        # generate CSV export
        self.stdout.write('Exporting CSV')
        data = self.get_data()  # get again because it's a generator
        with open('{}.csv'.format(base_filename), 'w') as csvfile:
            # write utf-8 byte order mark at the beginning of the file
            csvfile.write(codecs.BOM_UTF8.decode())

            csvwriter = csv.DictWriter(csvfile, fieldnames=self.csv_fields)
            csvwriter.writeheader()

            for row in data:
                csvwriter.writerow(self.flatten_dict(row))

    def get_data(self):
        # aggregate  data to be exported for use in generating
        # CSV and JSON output
        return StreamArray((self.event_data(event)
                            for event in Event.objects.all()),
                           Event.objects.count())

        # limit = 10000
        # # TODO: order? maybe by date by default?
        # return StreamArray((self.event_data(event)
        #                     for event in Event.objects.all()[:limit]),
        #                    limit)

    def event_data(self, event):
        '''Generate a dictionary of data to export for a single
         :class:`~mep.accounts.models.Event`'''

        # #: fields for CSV output
        #   csv_fields = [
        #       'member names', 'member sort names', 'member URIs', 'event type',
        #       'start date', 'end date', 'subscription category',
        #       'subscription volumes', 'subscription duration', 'subscription days',
        #       'price paid', 'refund', 'deposit',
        #       'work title',  # work URI TBD
        #       'edition title', 'borrow status', 'notes'
        #       'source', 'source manifest', 'source image'
        #   ]

        event_type = event.event_type
        data = OrderedDict([
            ('event type', event_type),
            ('start date', event.partial_start_date or ''),
            ('end date', event.partial_end_date or ''),
            ('member', OrderedDict()),
        ])
        members = event.account.persons.all()
        if members:
            data['member']['sort names'] = [m.sort_name for m in members]
            data['member']['names'] = [m.name for m in members]
            data['member']['URIs'] = [absolutize_url(m.get_absolute_url())
                                      for m in members]

        footnote = None

        # subscription-specific data
        if event_type in ['Subscription', 'Supplement', 'Renewal']:
            subs = event.subscription
            subscription_info = OrderedDict([
                ('price paid', '%s%.2f' % (subs.currency_symbol(),
                                           subs.price_paid or 0)),
                ('deposit', '%s%.2f' % (subs.currency_symbol(),
                                        subs.deposit or 0))
            ])
            if subs.duration:
                subscription_info['duration'] = subs.readable_duration()
                subscription_info['duration days'] = subs.duration
            if subs.volumes:
                subscription_info['volumes'] = int(subs.volumes)
            if subs.category:
                subscription_info['category'] = subs.category.name
            data['subscription'] = subscription_info

        elif event_type in 'Reimbursement' and event.reimbursement.refund:
            data['reimbursement'] = {
                'refund': '%s%.2f' %
                (event.reimbursement.currency_symbol(), event.reimbursement.refund)
            }
        elif event_type == 'Borrow':
            data['borrow'] = {'status': event.borrow.get_item_status_display()}
            footnote = event.borrow.footnotes.first()

        elif event_type == 'Purchase' and event.purchase.price:
            data['purchase'] = {
                'price': '%s%.2f' %
                (event.purchase.currency_symbol(), event.purchase.price)
            }
            footnote = event.purchase.footnotes.first()

        # generic event - check for footnotes
        else:
            footnote = footnote or event.event_footnotes.first()

        if event.work:
            item_info = OrderedDict([
                ('title', event.work.title),
            ])
            # TODO
            # if event.edition:
            #    item_info['edition title'] = event.
            if event.work.uri:
                item_info['work uri'] = event.work.uri
            if event.work.edition_uri:
                item_info['edition uri'] = event.work.edition_uri
            if event.work.public_notes:
                item_info['notes'] = event.work.public_notes

            data['item'] = item_info

        if event.notes:
            data['notes'] = event.notes

        if footnote:
            source_info = OrderedDict([
                ('citation', footnote.bibliography.bibliographic_note)
            ])
            if footnote.bibliography.manifest:
                source_info['manifest'] = footnote.bibliography.manifest.uri
                if footnote.image:
                    # FIXME: should this actually resolve to an image?
                    source_info['image'] = footnote.image.iiif_image_id
                    # image id in manifest: /full/1000,/0/default.jpg
                    # source_info['image'] = footnote.image.uri
            data['source'] = source_info

        return data

    def flatten_dict(self, data):
        '''Flatten a dictionary with nested dictionaries or lists into a
        key value pairs that can be output as CSV.  Nested dictionaries will be
        flattened and keys combined; lists will be converted into semi-colon
        delimited strings.'''
        flat_data = {}
        for key, val in data.items():
            # for a nested subdictionary, combine key and nested key
            if isinstance(val, dict):
                # TODO: recurse to handle lists in nested dicts
                for subkey, subval in val.items():
                    flat_data[' '.join([key, subkey])] = subval
            # convert list to a delimited string
            elif isinstance(val, list):
                flat_data[key] = ';'.join(val)
            else:
                flat_data[key] = val

        return flat_data


class StreamArray(list):
    '''Wrapper for a generator so it can be encoded as json'''
    # adapted from answer on
    # https://stackoverflow.com/questions/21663800/python-make-a-list-generator-json-serializable

    def __init__(self, gen, total):
        self.progbar = progressbar.ProgressBar(redirect_stdout=True,
                                               max_value=total)
        self.progress = 0
        self.gen = gen
        self.total = total

    def __iter__(self):
        for el in self.gen:
            self.progress += 1
            self.progbar.update(self.progress)
            yield el
        # mark progress bar as finished when iteration finishes
        self.progbar.finish()

    def __len__(self):
        return self.total
