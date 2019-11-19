import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.functions import Coalesce
from djiffy.models import Canvas, Manifest
from parasolr.django.indexing import ModelIndexable

from mep.common.models import Named, Notable


logger = logging.getLogger(__name__)


class BibliographySignalHandlers:
    '''Signal handlers for indexing :class:`Bibliography` records when
    related records are saved or deleted.'''

    @staticmethod
    def debug_log(name, count, mode='save'):
        # common method for debug logging with logic for singular people
        logger.debug('%s %s, reindexing %d related card%s',
                     mode, name, count, '' if count == 1 else 's')

    @staticmethod
    def person_save(sender=None, instance=None, raw=False, **kwargs):
        # raw = saved as presented; don't query the database
        if raw:
            return
        print('bibliography person save')
        if not instance.pk:
            return
        # find any cards associated via an account
        cards = Bibliography.objects.filter(account__persons__pk=instance.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('person', cards.count())
            ModelIndexable.index_items(cards)

    @staticmethod
    def person_delete(sender, instance, **kwargs):
        card_ids = Bibliography.objects \
            .filter(account__persons__pk=instance.pk) \
            .values_list('id', flat=True)
        if card_ids:
            # find the items based on the list of ids to reindex
            cards = Bibliography.objects.filter(id__in=list(card_ids))

            # clear the assocation so items will index without this person
            instance.account_set.clear()
            BibliographySignalHandlers.debug_log('person', cards.count(),
                                                 mode='delete')
            ModelIndexable.index_items(cards)

    @staticmethod
    def account_save(sender=None, instance=None, raw=False, **_kwargs):
        # raw = saved as presented; don't query the database
        if raw:
            return

        if not instance.pk:
            return
        # find any cards associated with this account
        cards = Bibliography.objects.filter(account__pk=instance.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('account', cards.count())
            ModelIndexable.index_items(cards)

    @staticmethod
    def account_delete(sender, instance, **kwargs):
        card_ids = Bibliography.objects.filter(account__pk=instance.pk) \
            .values_list('id', flat=True)

        if card_ids:
            # delete the assocation so cards will index without the account
            instance.card = None
            instance.save()
            # find the items based on the list of ids to reindex
            cards = Bibliography.objects.filter(id__in=list(card_ids))
            BibliographySignalHandlers.debug_log('account', cards.count(),
                                                 mode='delete')
            ModelIndexable.index_items(cards)

    @staticmethod
    def manifest_save(sender=None, instance=None, raw=False, **kwargs):
        # raw = saved as presented; don't query the database
        if raw:
            return

        if not instance.pk:
            return
        # find any cards associated with this account
        cards = Bibliography.objects.filter(manifest__pk=instance.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('manifest', cards.count())
            ModelIndexable.index_items(cards)

    @staticmethod
    def manifest_delete(sender, instance, **kwargs):
        card_ids = Bibliography.objects.filter(manifest__pk=instance.pk) \
            .values_list('id', flat=True)
        if card_ids:
            # delete the assocation so cards will index without the account
            instance.bibliography_set.clear()
            # find the items based on the list of ids to reindex
            cards = Bibliography.objects.filter(id__in=list(card_ids))
            BibliographySignalHandlers.debug_log('manifest', cards.count(),
                                                 mode='delete')
            ModelIndexable.index_items(cards)

    @staticmethod
    def canvas_save(_sender, instance, raw=False, **_kwargs):
        # raw = saved as presented; don't query the database
        if raw:
            return

        if not instance.pk:
            return
        # find any cards associated with this canvas, via manifest
        cards = Bibliography.objects.filter(manifest__pk=instance.manifest.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('canvas', cards.count())
            ModelIndexable.index_items(cards)

    @staticmethod
    def canvas_delete(sender, instance, **kwargs):
        cards = Bibliography.objects.filter(manifest__pk=instance.manifest.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('canvas', cards.count(),
                                                 mode='delete')
            ModelIndexable.index_items(cards)

    @staticmethod
    def event_save(_sender, instance, raw=False, **_kwargs):
        # raw = saved as presented; don't query the database
        if raw:
            return

        if not instance.pk:
            return
        # find any cards associated with this canvas, via manifest
        cards = Bibliography.objects.filter(account__pk=instance.account.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('event', cards.count())
            ModelIndexable.index_items(cards)

    @staticmethod
    def event_delete(sender, instance, **kwargs):
        cards = Bibliography.objects.filter(account__pk=instance.account.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('event', cards.count(),
                                                 mode='delete')
            ModelIndexable.index_items(cards)


class SourceType(Named, Notable):
    '''Type of source document.'''

    def item_count(self):
        '''number of associated bibliographic items'''
        return self.bibliography_set.count()
    item_count.short_description = '# items'


class Bibliography(Notable, ModelIndexable):
    # Note: citation might be better singular
    bibliographic_note = models.TextField(
        help_text='Full bibliographic citation')
    source_type = models.ForeignKey(SourceType)

    #: digital version as instance of :class:`djiffy.models.Manifest`
    manifest = models.ForeignKey(
        Manifest, blank=True, null=True, on_delete=models.SET_NULL,
        help_text='Digitized version of lending card, if locally available')

    class Meta:
        verbose_name_plural = 'Bibliographies'
        ordering = ('bibliographic_note',)

    def __str__(self):
        return self.bibliographic_note

    def footnote_count(self):
        '''number of footnotes this item is referenced in'''
        return self.footnote_set.count()
    footnote_count.short_description = '# footnotes'

    @classmethod
    def index_item_type(cls):
        """Label for this kind of indexable item."""
        # override default behavior (using model verbose name)
        # since we are only care about indexing cards, and not
        # all bibliography records
        return 'card'

    @classmethod
    def items_to_index(cls):
        '''Custom logic for finding items for bulk indexing; only include
        records associated with an account and with a IIIF manifest.'''
        return cls.objects.filter(account__isnull=False,
                                  manifest__isnull=False)

    index_depends_on = {
        'account_set': {
            'post_save': BibliographySignalHandlers.account_save,
            'pre_delete': BibliographySignalHandlers.account_delete
        },
        'account_set__persons': {
            'post_save': BibliographySignalHandlers.person_save,
            'pre_delete': BibliographySignalHandlers.person_delete
        },
        # NOTE: using app.Model notation here because
        # parasolr doesn't currently support foreignkey relation lookup
        'djiffy.Manifest': {
            'post_save': BibliographySignalHandlers.manifest_save,
            'pre_delete': BibliographySignalHandlers.manifest_delete
        },
        'djiffy.Canvas': {
            'post_save': BibliographySignalHandlers.canvas_save,
            'post_delete': BibliographySignalHandlers.canvas_delete
        },
        'accounts.Event': {
            'post_save': BibliographySignalHandlers.event_save,
            'post_delete': BibliographySignalHandlers.event_delete,
        },
        # unfortunately the generic event signals aren't fired
        # when subclass types are edited directly, so bind the same signal
        'accounts.Borrow': {
            'post_save': BibliographySignalHandlers.event_save,
            'post_delete': BibliographySignalHandlers.event_delete,
        },
        'accounts.Purchase': {
            'post_save': BibliographySignalHandlers.event_save,
            'post_delete': BibliographySignalHandlers.event_delete,
        },
        'accounts.Subscription': {
            'post_save': BibliographySignalHandlers.event_save,
            'post_delete': BibliographySignalHandlers.event_delete,
        },
        'accounts.Reimbursement': {
            'post_save': BibliographySignalHandlers.event_save,
            'post_delete': BibliographySignalHandlers.event_delete,
        }
    }

    def index_data(self):
        '''data for indexing in Solr'''
        index_data = super().index_data()
        # only library lending cards are indexed; if bibliography
        # does not have a manifest or is not associated with an account,
        # return id only.
        # This will blank out any previously indexed values, and item
        # will not be findable by any public searchable fields.
        account = self.account_set.all().first()
        if not self.manifest or not self.account_set.all().exists():
            del index_data['item_type']
            return index_data

        # we expect a thumbnail, but possible there is none
        if self.manifest.thumbnail:
            iiif_thumbnail = self.manifest.thumbnail.image

            # for now, store iiif thumbnail urls directly
            index_data['thumbnail_t'] = str(iiif_thumbnail.size(width=225))
            index_data['thumbnail2x_t'] = str(iiif_thumbnail.size(width=225 * 2))

        names = []
        account_years = set()
        for account in self.account_set.all():
            for person in account.persons.all():
                names.append(person.sort_name)
            account_years.update(set(date.year for date in
                                     account.event_dates))
        if names:
            index_data.update({
                'cardholder_t': names,
                'cardholder_sort_s': names[0],
            })

        if account_years:
            index_data.update({
                'years_is': list(account_years),
                'start_i': min(account_years),
                'end_i': max(account_years),
            })
        return index_data


class FootnoteQuerySet(models.QuerySet):
    '''Custom :class:`models.QuerySet` for :class:`Footnote`'''

    def event_date_range(self):
        '''Find earliest and latest dates for any events associated
        with footnotes in this queryset. Returns a tuple of earliest
        and latest dates, or None if no dates are found.'''

        # all related fields that could hold event dates
        date_fields = [
            'events__start_date', 'events__end_date',
            'borrows__start_date', 'borrows__end_date',
            'purchases__start_date', 'purchases__end_date'
        ]

        ## TODO exclude unknown years!
        values = self.annotate(
            start_dates=Coalesce(*date_fields),
            end_dates=Coalesce(*date_fields)) \
            .aggregate(first_date=models.Min('start_dates'),
                       last_date=models.Max('end_dates'))
        # return earliest and latest dates, unless result is None
        if values['first_date']:
            return values['first_date'], values['last_date']


class Footnote(Notable):
    '''Footnote that can be associated with any other model via
    generic relationship.  Used to provide supporting documentation
    for or against information in the system.
    '''
    bibliography = models.ForeignKey(Bibliography)
    location = models.TextField(
        blank=True,
        help_text='Page number for a book, URL for part of a website,' +
        ' or other location inside of a larger work.')
    snippet_text = models.TextField(blank=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        # restrict choices to "content" models (exclude django/admin models)
        # and models that are available in django admin
        # (otherwise, lookup is not possible)
        # TODO: add items here as the application expands
        limit_choices_to=models.Q(app_label='people',
            model__in=['country', 'person', 'address', 'profession']) |
            models.Q(
                app_label='accounts',
                model__in=['account', 'event', 'subscription', 'borrow',
                           'reimbursement', 'purchase']) |
            models.Q(app_label='books', model__in=['item'])
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    is_agree = models.BooleanField(
        'Supports', help_text='True if the evidence ' +
        'supports the information in the system, False if it contradicts.',
        default=True)

    image = models.ForeignKey(
        Canvas, blank=True, null=True,
        help_text='''Image location from an imported manifest, if available.''')

    # override default manager with customized version
    objects = FootnoteQuerySet.as_manager()

    def __str__(self):
        return 'Footnote on %s (%s)' % (self.content_object,
            ' '.join([str(i) for i in [self.bibliography, self.location] if i]))

    # NOTE: for convenient access from other models, add a
    # reverse generic relation
    #
    # from django.contrib.contenttypes.fields import GenericRelation
    # from mep.footnotes.models import Footnote
    #
    # footnotes = GenericRelation(Footnote)

    def image_thumbnail(self):
        '''Use admin thumbnail from image if available, but wrap
        in a link using rendering url from manifest when present'''
        if self.image:
            img = self.image.admin_thumbnail()
            if 'rendering' in self.image.manifest.extra_data:
                img = '<a target="_blank" href="%s">%s</a>' % \
                    (self.image.manifest.extra_data['rendering']['@id'], img)
            return img
    image_thumbnail.allow_tags = True



