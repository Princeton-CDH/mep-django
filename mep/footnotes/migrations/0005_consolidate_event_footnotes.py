# Generated by Django 2.2.11 on 2020-05-04 18:09

from django.contrib.auth.management import create_permissions
from django.db import migrations


def consolidate_event_footnotes(apps, schema_editor):
    Footnote = apps.get_model('footnotes', 'Footnote')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Event = apps.get_model('accounts', 'Event')

    # run create permissions for all accounts apps to ensure
    # that needed content types are created
    accounts_app_config = apps.get_app_config('accounts')
    accounts_app_config.models_module = True
    create_permissions(accounts_app_config, apps=apps, verbosity=0)
    accounts_app_config.models_module = None

    # for app_config in apps.get_app_configs():
    #     if app_config.name == 'accounts':
    #         app_config.models_module = True
    #         create_permissions(app_config, apps=apps, verbosity=0)
    #         app_config.models_module = None
    # get content types for the event models
    event_ctype = ContentType.objects.get(app_label='accounts', model='event')
    borrow_ctype = ContentType.objects.get(app_label='accounts',
                                           model='borrow')
    purchase_ctype = ContentType.objects.get(app_label='accounts',
                                             model='purchase')

    # update all footnotes linked to borrows to event content type
    # and event id for associated borrow
    for fn in Footnote.objects.filter(content_type=borrow_ctype):
        fn.content_type = event_ctype
        event = Event.objects.get(borrow__pk=fn.object_id)
        fn.object_id = event.pk
        fn.save()

    # same for footnotes on purchases
    for fn in Footnote.objects.filter(content_type=purchase_ctype):
        fn.content_type = event_ctype
        event = Event.objects.get(purchase__pk=fn.object_id)
        fn.object_id = event.pk
        fn.save()


class Migration(migrations.Migration):

    dependencies = [
        ('footnotes', '0004_on_delete'),
        ('accounts', '0031_on_delete'),
        ('contenttypes', '0002_remove_content_type_name')
    ]

    operations = [
        migrations.RunPython(
            code=consolidate_event_footnotes,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
