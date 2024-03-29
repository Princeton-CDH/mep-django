# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-08 19:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0005_people_address_to_account_address"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="infourl",
            options={"verbose_name": "Informational URL"},
        ),
        migrations.AlterModelOptions(
            name="location",
            options={},
        ),
        migrations.RemoveField(
            model_name="person",
            name="addresses",
        ),
        migrations.AddField(
            model_name="person",
            name="locations",
            field=models.ManyToManyField(
                blank=True, through="accounts.Address", to="people.Location"
            ),
        ),
        migrations.AlterField(
            model_name="infourl",
            name="url",
            field=models.URLField(
                help_text="Additional (non-VIAF) URLs for a person.", verbose_name="URL"
            ),
        ),
    ]
