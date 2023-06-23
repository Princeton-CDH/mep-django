# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-05 16:43
from __future__ import unicode_literals

from django.db import migrations, models
import mep.common.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("people", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Item",
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
                ("notes", models.TextField(blank=True)),
                ("mep_id", models.CharField(blank=True, max_length=255)),
                ("title", models.CharField(blank=True, max_length=255)),
                ("volume", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("number", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("year", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("season", models.CharField(blank=True, max_length=255)),
                ("edition", models.CharField(blank=True, max_length=255)),
                ("viaf_id", models.URLField(blank=True)),
                (
                    "authors",
                    models.ManyToManyField(related_name="authors", to="people.Person"),
                ),
                (
                    "editors",
                    models.ManyToManyField(related_name="editors", to="people.Person"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Publisher",
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
                ("name", models.CharField(max_length=255, unique=True)),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["name"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="PublisherPlace",
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
                ("name", models.CharField(max_length=255, unique=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "latitude",
                    models.DecimalField(
                        decimal_places=5,
                        max_digits=8,
                        validators=[mep.common.validators.verify_latlon],
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        decimal_places=5,
                        max_digits=8,
                        validators=[mep.common.validators.verify_latlon],
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="item",
            name="pub_places",
            field=models.ManyToManyField(blank=True, to="books.PublisherPlace"),
        ),
        migrations.AddField(
            model_name="item",
            name="publishers",
            field=models.ManyToManyField(blank=True, to="books.Publisher"),
        ),
        migrations.AddField(
            model_name="item",
            name="translators",
            field=models.ManyToManyField(
                related_name="translators", to="people.Person"
            ),
        ),
    ]
