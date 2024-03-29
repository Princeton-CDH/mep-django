# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-08-06 16:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0028_generic_event_partial_dates"),
        ("books", "0014_item_to_work"),
    ]

    operations = [
        # convert foreign key to integer to drop constraints but preserve data
        migrations.AlterField(
            model_name="event",
            name="item",
            field=models.IntegerField(blank=True, null=True),
        ),
        # rename the field from item to work
        migrations.RenameField(
            model_name="event",
            old_name="item",
            new_name="work",
        ),
        # alter event item to make new foreignkey to new work model
        migrations.AlterField(
            model_name="event",
            name="work",
            field=models.ForeignKey(
                blank=True,
                help_text="Work associated with this event, if any.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="books.Work",
            ),
        ),
    ]
