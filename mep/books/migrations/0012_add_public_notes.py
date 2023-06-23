# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-07-02 17:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("books", "0011_item_multiple_genres"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="public_notes",
            field=models.TextField(
                blank=True, help_text="Notes for display on the public website"
            ),
        ),
    ]
