# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-10-10 16:02
from __future__ import unicode_literals

from django.db import migrations
import wagtail.blocks
import wagtail.fields
import wagtail.documents.blocks
import wagtail.images.blocks


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0002_homepage_streamfield"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contentpage",
            name="body",
            field=wagtail.fields.StreamField(
                [
                    (
                        "paragraph",
                        wagtail.blocks.RichTextBlock(
                            features=[
                                "h3",
                                "h4",
                                "bold",
                                "italic",
                                "link",
                                "ol",
                                "ul",
                                "blockquote",
                            ]
                        ),
                    ),
                    (
                        "image",
                        wagtail.blocks.StructBlock(
                            [
                                ("image", wagtail.images.blocks.ImageChooserBlock()),
                                (
                                    "alternative_text",
                                    wagtail.blocks.TextBlock(
                                        help_text="Alternative text for visually impaired users to briefly communicate the intended message of the image in this context.",
                                        required=True,
                                    ),
                                ),
                                (
                                    "caption",
                                    wagtail.blocks.RichTextBlock(
                                        features=["bold", "italic", "link"],
                                        required=False,
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
        migrations.AlterField(
            model_name="homepage",
            name="body",
            field=wagtail.fields.StreamField(
                [
                    (
                        "paragraph",
                        wagtail.blocks.RichTextBlock(
                            features=[
                                "h3",
                                "h4",
                                "bold",
                                "italic",
                                "link",
                                "ol",
                                "ul",
                                "blockquote",
                            ]
                        ),
                    ),
                    (
                        "image",
                        wagtail.blocks.StructBlock(
                            [
                                ("image", wagtail.images.blocks.ImageChooserBlock()),
                                (
                                    "alternative_text",
                                    wagtail.blocks.TextBlock(
                                        help_text="Alternative text for visually impaired users to briefly communicate the intended message of the image in this context.",
                                        required=True,
                                    ),
                                ),
                                (
                                    "caption",
                                    wagtail.blocks.RichTextBlock(
                                        features=["bold", "italic", "link"],
                                        required=False,
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
        migrations.AlterField(
            model_name="landingpage",
            name="body",
            field=wagtail.fields.StreamField(
                [
                    (
                        "paragraph",
                        wagtail.blocks.RichTextBlock(
                            features=[
                                "h3",
                                "h4",
                                "bold",
                                "italic",
                                "link",
                                "ol",
                                "ul",
                                "blockquote",
                            ]
                        ),
                    ),
                    (
                        "image",
                        wagtail.blocks.StructBlock(
                            [
                                ("image", wagtail.images.blocks.ImageChooserBlock()),
                                (
                                    "alternative_text",
                                    wagtail.blocks.TextBlock(
                                        help_text="Alternative text for visually impaired users to briefly communicate the intended message of the image in this context.",
                                        required=True,
                                    ),
                                ),
                                (
                                    "caption",
                                    wagtail.blocks.RichTextBlock(
                                        features=["bold", "italic", "link"],
                                        required=False,
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
