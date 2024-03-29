# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-08-06 21:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("books", "0014_item_to_work"),
        ("accounts", "0029_event_item_to_work"),
    ]

    operations = [
        migrations.CreateModel(
            name="Edition",
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
                (
                    "title",
                    models.CharField(
                        blank=True,
                        help_text="Title of this edition, if different from associated work",
                        max_length=255,
                    ),
                ),
                ("volume", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("number", models.PositiveSmallIntegerField(blank=True, null=True)),
                (
                    "year",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        help_text="Date of Publication for this edition",
                        null=True,
                    ),
                ),
                ("season", models.CharField(blank=True, max_length=255)),
                ("edition", models.CharField(blank=True, max_length=255)),
                (
                    "uri",
                    models.URLField(
                        blank=True,
                        help_text="Linked data URI for this edition, if known",
                        verbose_name="URI",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="EditionCreator",
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
                (
                    "creator_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="books.CreatorType",
                    ),
                ),
                (
                    "edition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="books.Edition"
                    ),
                ),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="people.Person"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.RemoveField(
            model_name="work",
            name="edition",
        ),
        migrations.RemoveField(
            model_name="work",
            name="number",
        ),
        migrations.RemoveField(
            model_name="work",
            name="pub_places",
        ),
        migrations.RemoveField(
            model_name="work",
            name="publishers",
        ),
        migrations.RemoveField(
            model_name="work",
            name="season",
        ),
        migrations.RemoveField(
            model_name="work",
            name="volume",
        ),
        migrations.AlterField(
            model_name="work",
            name="title",
            field=models.CharField(
                blank=True, help_text="Title of the work in English", max_length=255
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="work_format",
            field=models.ForeignKey(
                blank=True,
                help_text="Format, e.g. book or periodical",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="books.Format",
                verbose_name="Format",
            ),
        ),
        migrations.AddField(
            model_name="edition",
            name="creators",
            field=models.ManyToManyField(
                through="books.EditionCreator", to="people.Person"
            ),
        ),
        migrations.AddField(
            model_name="edition",
            name="pub_places",
            field=models.ManyToManyField(
                blank=True,
                to="books.PublisherPlace",
                verbose_name="Places of Publication",
            ),
        ),
        migrations.AddField(
            model_name="edition",
            name="publisher",
            field=models.ManyToManyField(blank=True, to="books.Publisher"),
        ),
        migrations.AddField(
            model_name="edition",
            name="work",
            field=models.ForeignKey(
                help_text="Generic Work associated with this edition.",
                on_delete=django.db.models.deletion.CASCADE,
                to="books.Work",
            ),
        ),
    ]
