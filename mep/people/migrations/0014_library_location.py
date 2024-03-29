# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2019-11-05 20:45
from __future__ import unicode_literals

from django.db import migrations


def add_library_address(apps, schema_editor):
    # adds the known location for the Shakespeare and Company lending library
    # as a Location, so it can be used to draw the library's pin on maps
    Location = apps.get_model("people", "Location")
    Location.objects.get_or_create(
        name="Shakespeare and Company",
        city="Paris",
        street_address="12 rue de l’Odéon",
        latitude=48.85089,
        longitude=2.338502,
        notes="location from 1921-1941",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0013_rename_sex_to_gender"),
    ]

    operations = [
        migrations.RunPython(
            add_library_address, reverse_code=migrations.RunPython.noop
        )
    ]
