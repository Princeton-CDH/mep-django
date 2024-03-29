# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-12 14:40
from __future__ import unicode_literals

from django.db import migrations, transaction
import mep.accounts.partial_date


def copy_precisions(apps, schema_editor):
    """Copy Borrow and Purchase date precisions over to Event"""
    Event = apps.get_model("accounts", "Event")

    for related_name in ("purchase", "borrow"):
        # get all events with purchase and borrow events and
        # pull over related fields to temporary ones on Event
        events = Event.objects.filter(
            **{"%s__isnull" % related_name: False}
        ).select_related(related_name)
        # wrap in atomic transaction to avoid commits on every save
        with transaction.atomic():
            for event in events:
                # copy over start and end date precision
                event.temp_start_date_precision = getattr(
                    event, related_name
                ).start_date_precision
                event.temp_end_date_precision = getattr(
                    event, related_name
                ).end_date_precision
                event.save()


def revert_copy_precisions(apps, schema_editor):
    """Revert the copy of dates from Borrow and Purchase to Event."""
    Event = apps.get_model("accounts", "Event")

    for related_name in ("purchase", "borrow"):
        events = Event.objects.filter(
            **{"%s__isnull" % related_name: False}
        ).select_related(related_name)
        with transaction.atomic():
            for event in events:
                related = getattr(event, related_name)
                related.start_date_precision = event.temp_start_date_precision
                related.end_date_precision = event.temp_end_date_precision
                related.save()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0027_address_partial_dates"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="temp_end_date_precision",
            field=mep.accounts.partial_date.DatePrecisionField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="event",
            name="temp_start_date_precision",
            field=mep.accounts.partial_date.DatePrecisionField(blank=True, null=True),
        ),
        migrations.RunPython(copy_precisions, reverse_code=revert_copy_precisions),
        migrations.RemoveField(
            model_name="borrow",
            name="end_date_precision",
        ),
        migrations.RemoveField(
            model_name="borrow",
            name="start_date_precision",
        ),
        migrations.RemoveField(
            model_name="purchase",
            name="end_date_precision",
        ),
        migrations.RemoveField(
            model_name="purchase",
            name="start_date_precision",
        ),
        migrations.RenameField(
            model_name="event",
            old_name="temp_end_date_precision",
            new_name="end_date_precision",
        ),
        migrations.RenameField(
            model_name="event",
            old_name="temp_start_date_precision",
            new_name="start_date_precision",
        ),
    ]
