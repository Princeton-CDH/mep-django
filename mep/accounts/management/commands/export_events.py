'''
Manage command to export event data for use by others.

Generates a CSV and JSON file including details on every event in the
database with summary details and URIs for associated library member(s)
and book (for events linked to books).

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
        'event_type',
        'start_date', 'end_date',
        'member_uris', 'member_names', 'member_sort_names',
        # subscription specific
        'subscription_price_paid', 'subscription_deposit',
        'subscription_duration', 'subscription_duration_days',
        'subscription_volumes', 'subscription_category',
        'subscription_purchase_date',
        # reimbursement specific
        'reimbursement_refund',
        # borrow specific
        'borrow_status', 'borrow_duration_days',
        # purchase specific
        'purchase_price',
        # currency applies to purchase, borrow, and subscription
        'currency',
        # related book/item
        'item_uri', 'item_title', 'item_volume', 'item_authors',
        'item_year', 'item_notes',
        # footnote/citation
        'source_type', 'source_citation', 'source_manifest', 'source_image'
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
            # use event label instead of type for more detail on some generics
            ('event_type', obj.event_label),
            ('start_date', obj.partial_start_date or ''),
            ('end_date', obj.partial_end_date or ''),
            ('member', OrderedDict()),
        ])
        member_info = self.member_info(obj)
        if member_info:
            data['member'] = member_info

        currency = None

        # subscription-specific data
        if event_type in ['Subscription', 'Supplement', 'Renewal',
                          'Separate Deposit']:
            data['subscription'] = self.subscription_info(obj)
            currency = obj.subscription.currency

        # reimbursement data
        elif event_type in 'Reimbursement' and obj.reimbursement.refund:
            data['reimbursement'] = {
                'refund': '%.2f' % obj.reimbursement.refund
            }
            currency = obj.reimbursement.currency

        # borrow data
        elif event_type == 'Borrow':
            data['borrow'] = {
                'status': obj.borrow.get_item_status_display()
            }
            borrow_duration = obj.calculate_duration()
            if borrow_duration:
                data['borrow']['duration_days'] = borrow_duration

        # purchase data
        elif event_type == 'Purchase' and obj.purchase.price:
            data['purchase'] = {
                'price': '%.2f' % obj.purchase.price
            }
            currency = obj.purchase.currency

        if currency:
            data['currency'] = currency

        item_info = self.item_info(obj)
        if item_info:
            data['item'] = item_info
        # footnote should always be attached to the base event;
        # multiple footnotes should be supported
        if obj.footnotes.exists():
            data['source'] = [self.source_info(fn)
                              for fn in obj.footnotes.all()]
        return data

    def member_info(self, event):
        '''Event about member(s) for the account associated with an event.'''
        members = event.account.persons.all()
        # return if no member attached
        if not members:
            return

        return OrderedDict([
            ('uris', [absolutize_url(m.get_absolute_url()) for m in members]),
            ('names', [m.name for m in members]),
            ('sort_names', [m.sort_name for m in members])
        ])

    def subscription_info(self, event):
        '''subscription details for an event'''
        # bail out if this event is not a subscription
        try:
            subs = event.subscription
        except ObjectDoesNotExist:
            return

        info = OrderedDict()
        if subs.price_paid:
            info['price_paid'] = '%.2f' % subs.price_paid
        if subs.deposit:
            info['deposit'] = '%.2f' % subs.deposit

        if subs.duration:
            info['duration'] = subs.readable_duration()
            info['duration_days'] = subs.duration
        if subs.volumes:
            info['volumes'] = int(subs.volumes)
        if subs.category:
            info['category'] = subs.category.name
        if subs.purchase_date:
            info['purchase_date'] = subs.partial_purchase_date
        return info

    def item_info(self, event):
        '''associated work details for an event'''
        if event.work:
            item_info = OrderedDict([
                ('uri', absolutize_url(event.work.get_absolute_url())),
                ('title', event.work.title),
            ])
            if event.edition:
                item_info['volume'] = event.edition.display_text()
            if event.work.authors:
                item_info['authors'] = [a.sort_name
                                        for a in event.work.authors]
            if event.work.year:
                item_info['year'] = event.work.year
            if event.work.public_notes:
                item_info['notes'] = event.work.public_notes

            return item_info

    def source_info(self, footnote):
        '''source details from a footnote'''
        source_info = OrderedDict([
            ('type', footnote.bibliography.source_type.name),
            ('citation', footnote.bibliography.bibliographic_note)
        ])
        if footnote.bibliography.manifest:
            source_info['manifest'] = footnote.bibliography.manifest.uri
            if footnote.image:
                # default iiif image
                source_info['image'] = str(footnote.image.image)
        return source_info
