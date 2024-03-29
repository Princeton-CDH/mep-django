# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-27 01:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("footnotes", "0001_initial"),
        ("accounts", "0020_convert_bought_to_item_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="card",
            field=models.ForeignKey(
                blank=True,
                help_text="Lending Library Card for this account",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="footnotes.Bibliography",
            ),
        ),
    ]
