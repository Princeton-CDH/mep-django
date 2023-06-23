# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-11 17:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="address",
            name="name",
            field=models.CharField(
                blank=True,
                help_text="Name of the place if there is one, e.g. Savoy Hotel, British Embassy, Villa Trianon",
                max_length=255,
                verbose_name="Name of location",
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="addresses",
            field=models.ManyToManyField(
                blank=True,
                help_text="Autocomplete searches on all fields except latitude and longitude.",
                to="people.Address",
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="viaf_id",
            field=models.URLField(
                blank=True,
                help_text="Canonical VIAF URI for this person",
                verbose_name="VIAF id",
            ),
        ),
    ]
