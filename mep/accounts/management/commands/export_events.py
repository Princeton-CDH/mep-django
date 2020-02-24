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

from django.db.models.functions import Coalesce
from django.core.exceptions import ObjectDoesNotExist
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
        'item title', 'item work uri', 'item volume',
        'item notes',
        # generic
        'notes',
        # footnote/citation
        'source citation', 'source manifest', 'source image'
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '-d', '--directory',
            help='Specify the directory where files should be generated')
        parser.add_argument(
            '-m', '--max', type=int,
            help='Maximum number of events to export (for testing)')

    def handle(self, *args, **kwargs):
        base_filename = 'events'
        if kwargs['directory']:
            base_filename = os.path.join(kwargs['directory'], base_filename)

        # generate filenames based on slug ?
        # Can we use the same data to generate both CSV and JSON?
        data = self.get_data(kwargs.get('max'))
        self.stdout.write('Exporting JSON')
        # list of dictionaries can be output as is for JSON export
        with open('{}.json'.format(base_filename), 'w') as jsonfile:
            for chunk in json.JSONEncoder(indent=2).iterencode(data):
                jsonfile.write(chunk)

        # generate CSV export
        self.stdout.write('Exporting CSV')
        # need to get the data again, since it's a generator
        data = self.get_data(kwargs.get('max'))
        with open('{}.csv'.format(base_filename), 'w') as csvfile:
            # write utf-8 byte order mark at the beginning of the file
            csvfile.write(codecs.BOM_UTF8.decode())

            csvwriter = csv.DictWriter(csvfile, fieldnames=self.csv_fields)
            csvwriter.writeheader()

            for row in data:
                csvwriter.writerow(self.flatten_dict(row))

    def get_data(self, maximum=None):
        '''get event objects to be exported'''
        # Order events by date. Order on precision first so unknown dates
        # will be last, then sort by first known date of start/end.
        events = Event.objects.all() \
            .order_by(Coalesce('start_date_precision', 'end_date_precision'),
                      Coalesce('start_date', 'end_date').asc(nulls_last=True))
        # grab the first N if maximum is specified
        if maximum:
            events = events[:maximum]
        return StreamArray((self.event_data(event) for event in events),
                           events.count())

    def event_data(self, event):
        '''Generate a dictionary of data to export for a single
         :class:`~mep.accounts.models.Event`'''
        event_type = event.event_type
        data = OrderedDict([
            ('event type', event_type),
            ('start date', event.partial_start_date or ''),
            ('end date', event.partial_end_date or ''),
            ('member', OrderedDict()),
        ])
        member_info = self.member_info(event)
        if member_info:
            data['member'] = member_info

        # variable to store footnote reference, if any
        footnote = None

        # subscription-specific data
        if event_type in ['Subscription', 'Supplement', 'Renewal']:
            data['subscription'] = self.subscription_info(event)

        # reimbursement data
        elif event_type in 'Reimbursement' and event.reimbursement.refund:
            data['reimbursement'] = {
                'refund': '%s%.2f' %
                (event.reimbursement.currency_symbol(), event.reimbursement.refund)
            }

        # borrow data
        elif event_type == 'Borrow':
            data['borrow'] = {
                'status': event.borrow.get_item_status_display()
            }
            # capture a footnote if there is one
            footnote = event.borrow.footnotes.first()

        # purchase data
        elif event_type == 'Purchase' and event.purchase.price:
            data['purchase'] = {
                'price': '%s%.2f' %
                (event.purchase.currency_symbol(), event.purchase.price)
            }
            footnote = event.purchase.footnotes.first()

        # check for footnote on the generic event if one was not already found
        footnote = footnote or event.event_footnotes.first()

        item_info = self.item_info(event)
        if item_info:
            data['item'] = item_info
        if event.notes:
            data['notes'] = event.notes
        if footnote:
            data['source'] = self.source_info(footnote)
        return data

    def member_info(self, event):
        '''Event about member(s) for the account associated with an event.'''
        members = event.account.persons.all()
        # return if no member attached
        if not members:
            return

        return OrderedDict([
            ('sort names', [m.sort_name for m in members]),
            ('names', [m.name for m in members]),
            ('URIs', [absolutize_url(m.get_absolute_url()) for m in members])
        ])

    def subscription_info(self, event):
        '''subscription details for an event'''
        # bail out if this event is not a subscription
        try:
            subs = event.subscription
        except ObjectDoesNotExist:
            return

        info = OrderedDict([
            ('price paid', '%s%.2f' % (subs.currency_symbol(),
                                       subs.price_paid or 0)),
            ('deposit', '%s%.2f' % (subs.currency_symbol(),
                                    subs.deposit or 0))
        ])
        if subs.duration:
            info['duration'] = subs.readable_duration()
            info['duration days'] = subs.duration
        if subs.volumes:
            info['volumes'] = int(subs.volumes)
        if subs.category:
            info['category'] = subs.category.name
        return info

    def item_info(self, event):
        if event.work:
            item_info = OrderedDict([
                ('title', event.work.title),
            ])
            if event.edition:
                # NOTE: using string representation for now,
                # will revisit to refine later
                item_info['volume'] = str(event.edition)
            if event.work.uri:
                item_info['work uri'] = event.work.uri
            if event.work.public_notes:
                item_info['notes'] = event.work.public_notes

            return item_info

    def source_info(self, footnote):
        '''source details from a footnote'''
        source_info = OrderedDict([
            ('citation', footnote.bibliography.bibliographic_note)
        ])
        if footnote.bibliography.manifest:
            source_info['manifest'] = footnote.bibliography.manifest.uri
            if footnote.image:
                # default iiif image
                source_info['image'] = str(footnote.image.image)
        return source_info

    def flatten_dict(self, data):
        '''Flatten a dictionary with nested dictionaries or lists into a
        key value pairs that can be output as CSV.  Nested dictionaries will be
        flattened and keys combined; lists will be converted into semi-colon
        delimited strings.'''
        flat_data = {}
        for key, val in data.items():
            # for a nested subdictionary, combine key and nested key
            if isinstance(val, dict):
                # recurse to handle lists in nested dicts
                for subkey, subval in self.flatten_dict(val).items():
                    flat_data[' '.join([key, subkey])] = subval
            # convert list to a delimited string
            elif isinstance(val, list):
                flat_data[key] = ';'.join(val)
            else:
                flat_data[key] = val

        return flat_data


class StreamArray(list):
    '''Wrapper for a generator so data can be streamed and encoded as json.
    Includes progressbar output that updates as the generator is consumed.


    :param gen: generator with data to be exported
    :param total: total number of items in the generator, for
        initializing the progress bar
    '''

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
