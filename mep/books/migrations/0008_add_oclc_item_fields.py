# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-02 20:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("books", "0007_item_updated_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subject",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "uri",
                    models.URLField(
                        help_text="Subject URI", unique=True, verbose_name="URI"
                    ),
                ),
                ("rdf_type", models.URLField(verbose_name="RDF Type")),
            ],
        ),
        migrations.AddField(
            model_name="item",
            name="edition_uri",
            field=models.URLField(
                blank=True,
                help_text="Linked data URI for this edition, if known",
                verbose_name="Edition URI",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="genre",
            field=models.CharField(
                blank=True, help_text="Genre from OCLC Work record", max_length=255
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="item_type",
            field=models.CharField(
                blank=True,
                help_text="Type of item, e.g. book or periodical",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="uri",
            field=models.URLField(
                blank=True,
                help_text="Linked data URI for this work",
                verbose_name="Work URI",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="subjects",
            field=models.ManyToManyField(blank=True, to="books.Subject"),
        ),
    ]
