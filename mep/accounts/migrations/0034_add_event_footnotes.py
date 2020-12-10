# Generated by Django 2.2.11 on 2020-12-08 14:53

from django.db import migrations
from django.contrib.admin.models import ADDITION
from django.conf import settings


def add_missing_footnotes(apps, schema_editor):
    '''
    Add footnotes to document source for events without footnotes.
    Events should be associated with one of two address books based on
    P36ADD and 36ADD tags in the event notes; all other events without
    footnotes are from the logbooks.
    '''
    Bibliography = apps.get_model('footnotes', 'Bibliography')
    Footnote = apps.get_model('footnotes', 'Footnote')
    Event = apps.get_model('accounts', 'Event')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    User = apps.get_model('auth', 'User')
    LogEntry = apps.get_model('admin', 'LogEntry')

    event_content_type = ContentType.objects \
        .get(model='event', app_label='accounts')
    footnote_content_type = ContentType.objects \
        .get(model='footnote', app_label='footnotes')
    script_user = User.objects.get(username=settings.SCRIPT_USERNAME)

    # get bibliographic entries to be used as sources for footnotes
    # (but handle case where they don't exist, in a new db)
    addressbook_1936 = Bibliography.objects \
        .filter(bibliographic_note__contains="Address Book 1919–1935",
                source_type__name='Address Book').first()
    addressbook_post1936 = Bibliography.objects \
        .filter(bibliographic_note__contains="Address Book 1935–1937",
                source_type__name='Address Book').first()
    logbooks = Bibliography.objects \
        .filter(bibliographic_note__contains="Logbooks 1919–1941",
                source_type__name='Logbook').first()

    # because footnote is a generic relation, it can't be used in a
    # queryset filter in a migration; instead, get a list event ids
    # with footnotes, so we can exclude them
    events_with_footnotes = Footnote.objects \
        .filter(content_type=event_content_type) \
        .values_list('object_id')

    if addressbook_post1936:
        # find all events with tag P36ADD and no footnote
        events_post36add = Event.objects.filter(notes__contains='P36ADD') \
                                        .exclude(pk__in=events_with_footnotes)
        # for each event: create footnote, then create log entry for the footnote
        # NOTE: not using bulk create because the objects it returns don't have pks
        for event in events_post36add:
            footnote = Footnote.objects.create(
                bibliography=addressbook_post1936,
                content_type=event_content_type,
                object_id=event.pk)
            LogEntry.objects.create(
                user_id=script_user.id,
                content_type_id=footnote_content_type.pk,
                object_id=footnote.pk,
                object_repr='Footnote on event %s for %s' %
                            (event.pk, addressbook_post1936.bibliographic_note),
                change_message='Address book footnote created based on P36ADD tag',
                action_flag=ADDITION)

    if addressbook_1936:
        # find events from the 1936 address book; exclude events from
        # post-1936 address book or tha talready have
        events_36add = Event.objects.filter(notes__contains='36ADD') \
                            .exclude(notes__contains='P36ADD') \
                            .exclude(pk__in=events_with_footnotes)
        # for each event: create footnote, then create log entry for the footnote
        for event in events_36add:
            footnote = Footnote.objects.create(
                bibliography=addressbook_1936,
                content_type=event_content_type,
                object_id=event.pk)
            LogEntry.objects.create(
                user_id=script_user.id,
                content_type_id=footnote_content_type.pk,
                object_id=footnote.pk,
                object_repr='Footnote on event %s for %s' %
                            (event.pk, addressbook_1936.bibliographic_note),
                change_message='Address book footnote created based on 36ADD tag',
                action_flag=ADDITION)

    if logbooks:
        # find all remaining events without footnotes — from the logbooks
        logbooks_events = Event.objects.exclude(notes__contains='36ADD') \
                               .exclude(pk__in=events_with_footnotes)
        for event in logbooks_events:
            footnote = Footnote.objects.create(
                bibliography=logbooks,
                content_type=event_content_type,
                object_id=event.pk)
            LogEntry.objects.create(
                user_id=script_user.id,
                content_type_id=footnote_content_type.pk,
                object_id=footnote.pk,
                object_repr='Footnote on event %s for %s' %
                            (event.pk, logbooks.bibliographic_note),
                change_message='Associated with logbooks',
                action_flag=ADDITION)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0033_subscription_purchase_date_adjustments'),
        ('footnotes', '0005_consolidate_event_footnotes'),
        ('admin', '0003_logentry_add_action_flag_choices'),
        ('common', '0005_create_script_user')
    ]

    operations = [
        migrations.RunPython(add_missing_footnotes,
                             migrations.RunPython.noop)
    ]
