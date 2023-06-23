# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-17 21:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0016_add_borrow_date_precision"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="borrow",
            name="purchase_id",
        ),
        migrations.AddField(
            model_name="borrow",
            name="bought",
            field=models.BooleanField(
                default=False, help_text="Item was bought instead of returned"
            ),
        ),
    ]
