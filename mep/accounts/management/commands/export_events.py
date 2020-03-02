'''
Manage command to export event data for use by others.

Generates a CSV and JSON file including details on every event in the
database with summary details and URIs for associated library member(s)
and book (for events linked to books).

Takes an optional argument to specify the output directory. Otherwise,
files are created in the current directory.

'''

from collections import OrderedDict

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import Coalesce

from mep.accounts.models import Event
from mep.common.management.export import BaseExport
from mep.common.utils import absolutize_url


class Command(BaseExport):
    '''Export event data.'''
    help = __doc__

    model = Event

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

    def get_queryset(self):
        '''get event objects to be exported'''
        # Order events by date. Order on precision first so unknown dates
        # will be last, then sort by first known date of start/end.
        return Event.objects.all() \
            .order_by(Coalesce('start_date_precision', 'end_date_precision'),
                      Coalesce('start_date', 'end_date').asc(nulls_last=True))

    def get_object_data(self, obj):
        '''Generate a dictionary of data to export for a single
         :class:`~mep.accounts.models.Event`'''
        event_type = obj.event_type
        data = OrderedDict([
            ('event type', event_type),
            ('start date', obj.partial_start_date or ''),
            ('end date', obj.partial_end_date or ''),
            ('member', OrderedDict()),
        ])
        member_info = self.member_info(obj)
        if member_info:
            data['member'] = member_info

        # variable to store footnote reference, if any
        footnote = None

        # subscription-specific data
        if event_type in ['Subscription', 'Supplement', 'Renewal']:
            data['subscription'] = self.subscription_info(obj)

        # reimbursement data
        elif event_type in 'Reimbursement' and obj.reimbursement.refund:
            data['reimbursement'] = {
                'refund': '%s%.2f' %
                          (obj.reimbursement.currency_symbol(),
                           obj.reimbursement.refund)
            }

        # borrow data
        elif event_type == 'Borrow':
            data['borrow'] = {
                'status': obj.borrow.get_item_status_display()
            }
            # capture a footnote if there is one
            footnote = obj.borrow.footnotes.first()

        # purchase data
        elif event_type == 'Purchase' and obj.purchase.price:
            data['purchase'] = {
                'price': '%s%.2f' %
                         (obj.purchase.currency_symbol(), obj.purchase.price)
            }
            footnote = obj.purchase.footnotes.first()

        # check for footnote on the generic event if one was not already found
        footnote = footnote or obj.event_footnotes.first()

        item_info = self.item_info(obj)
        if item_info:
            data['item'] = item_info
        if obj.notes:
            data['notes'] = obj.notes
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
        '''associated work details for an event'''
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
