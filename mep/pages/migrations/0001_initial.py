# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-02-05 22:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import wagtail.blocks
import wagtail.fields
import wagtail.documents.blocks
import wagtail.images.blocks


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("wagtailimages", "0021_image_file_hash"),
        ("wagtailcore", "0040_page_draft_title"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.Page",
                    ),
                ),
                (
                    "body",
                    wagtail.fields.StreamField(
                        [
                            ("paragraph", wagtail.blocks.RichTextBlock()),
                            ("image", wagtail.images.blocks.ImageChooserBlock()),
                            (
                                "captioned_image",
                                wagtail.blocks.StructBlock(
                                    [
                                        (
                                            "image",
                                            wagtail.images.blocks.ImageChooserBlock(),
                                        ),
                                        (
                                            "caption",
                                            wagtail.blocks.RichTextBlock(
                                                features=["bold", "italic", "link"]
                                            ),
                                        ),
                                    ]
                                ),
                            ),
                            (
                                "document",
                                wagtail.documents.blocks.DocumentChooserBlock(),
                            ),
                            (
                                "footnotes",
                                wagtail.blocks.RichTextBlock(
                                    classname="footnotes",
                                    features=["ol", "ul", "bold", "italic", "link"],
                                ),
                            ),
                        ]
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
        migrations.CreateModel(
            name="HomePage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.Page",
                    ),
                ),
                ("body", wagtail.fields.RichTextField(blank=True)),
            ],
            options={
                "verbose_name": "homepage",
            },
            bases=("wagtailcore.page",),
        ),
        migrations.CreateModel(
            name="LandingPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.Page",
                    ),
                ),
                ("tagline", models.CharField(max_length=500)),
                (
                    "body",
                    wagtail.fields.StreamField(
                        [
                            ("paragraph", wagtail.blocks.RichTextBlock()),
                            ("image", wagtail.images.blocks.ImageChooserBlock()),
                            (
                                "captioned_image",
                                wagtail.blocks.StructBlock(
                                    [
                                        (
                                            "image",
                                            wagtail.images.blocks.ImageChooserBlock(),
                                        ),
                                        (
                                            "caption",
                                            wagtail.blocks.RichTextBlock(
                                                features=["bold", "italic", "link"]
                                            ),
                                        ),
                                    ]
                                ),
                            ),
                            (
                                "document",
                                wagtail.documents.blocks.DocumentChooserBlock(),
                            ),
                            (
                                "footnotes",
                                wagtail.blocks.RichTextBlock(
                                    classname="footnotes",
                                    features=["ol", "ul", "bold", "italic", "link"],
                                ),
                            ),
                        ]
                    ),
                ),
                (
                    "header_image",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="wagtailimages.Image",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
    ]
