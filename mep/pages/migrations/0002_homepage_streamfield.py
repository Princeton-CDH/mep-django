# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-02-05 22:41
from __future__ import unicode_literals

from django.db import migrations
import wagtail.blocks
import wagtail.fields
import wagtail.documents.blocks
import wagtail.images.blocks


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="homepage",
            name="body",
            field=wagtail.fields.StreamField(
                [
                    ("paragraph", wagtail.blocks.RichTextBlock()),
                    ("image", wagtail.images.blocks.ImageChooserBlock()),
                    (
                        "captioned_image",
                        wagtail.blocks.StructBlock(
                            [
                                ("image", wagtail.images.blocks.ImageChooserBlock()),
                                (
                                    "caption",
                                    wagtail.blocks.RichTextBlock(
                                        features=["bold", "italic", "link"]
                                    ),
                                ),
                            ]
                        ),
                    ),
                    ("document", wagtail.documents.blocks.DocumentChooserBlock()),
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
    ]
