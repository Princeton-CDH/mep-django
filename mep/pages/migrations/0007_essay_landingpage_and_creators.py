# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-11-14 21:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import mep.pages.models
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.documents.blocks
import wagtail.images.blocks
import wagtail.snippets.blocks


class Migration(migrations.Migration):
    dependencies = [
        ("wagtailimages", "0021_image_file_hash"),
        ("wagtailcore", "0040_page_draft_title"),
        ("pages", "0006_add_svg_image_block"),
    ]

    operations = [
        migrations.CreateModel(
            name="EssayLandingPage",
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
                    wagtail.core.fields.StreamField(
                        [
                            (
                                "paragraph",
                                wagtail.core.blocks.RichTextBlock(
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
                                wagtail.core.blocks.StructBlock(
                                    [
                                        (
                                            "image",
                                            wagtail.images.blocks.ImageChooserBlock(),
                                        ),
                                        (
                                            "alternative_text",
                                            wagtail.core.blocks.TextBlock(
                                                help_text="Alternative text for visually impaired users to\nbriefly communicate the intended message of the image in this context.",
                                                required=True,
                                            ),
                                        ),
                                        (
                                            "caption",
                                            wagtail.core.blocks.RichTextBlock(
                                                features=["bold", "italic", "link"],
                                                required=False,
                                            ),
                                        ),
                                    ]
                                ),
                            ),
                            (
                                "svg_image",
                                wagtail.core.blocks.StructBlock(
                                    [
                                        (
                                            "image",
                                            wagtail.documents.blocks.DocumentChooserBlock(),
                                        ),
                                        (
                                            "alternative_text",
                                            wagtail.core.blocks.TextBlock(
                                                help_text="Alternative text for visually impaired users to\nbriefly communicate the intended message of the image in this context.",
                                                required=True,
                                            ),
                                        ),
                                        (
                                            "caption",
                                            wagtail.core.blocks.RichTextBlock(
                                                features=["bold", "italic", "link"],
                                                required=False,
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
                                wagtail.core.blocks.RichTextBlock(
                                    classname="footnotes",
                                    features=["ol", "ul", "bold", "italic", "link"],
                                ),
                            ),
                        ],
                        blank=True,
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
            bases=(mep.pages.models.RdfPageMixin, "wagtailcore.page"),
        ),
        migrations.CreateModel(
            name="EssayPage",
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
                    "description",
                    wagtail.core.fields.RichTextField(
                        blank=True,
                        help_text="Optional. Brief description for preview display. Will also be used for search description (without tags), if one is not entered.",
                    ),
                ),
                (
                    "body",
                    wagtail.core.fields.StreamField(
                        [
                            (
                                "paragraph",
                                wagtail.core.blocks.RichTextBlock(
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
                                wagtail.core.blocks.StructBlock(
                                    [
                                        (
                                            "image",
                                            wagtail.images.blocks.ImageChooserBlock(),
                                        ),
                                        (
                                            "alternative_text",
                                            wagtail.core.blocks.TextBlock(
                                                help_text="Alternative text for visually impaired users to\nbriefly communicate the intended message of the image in this context.",
                                                required=True,
                                            ),
                                        ),
                                        (
                                            "caption",
                                            wagtail.core.blocks.RichTextBlock(
                                                features=["bold", "italic", "link"],
                                                required=False,
                                            ),
                                        ),
                                    ]
                                ),
                            ),
                            (
                                "svg_image",
                                wagtail.core.blocks.StructBlock(
                                    [
                                        (
                                            "image",
                                            wagtail.documents.blocks.DocumentChooserBlock(),
                                        ),
                                        (
                                            "alternative_text",
                                            wagtail.core.blocks.TextBlock(
                                                help_text="Alternative text for visually impaired users to\nbriefly communicate the intended message of the image in this context.",
                                                required=True,
                                            ),
                                        ),
                                        (
                                            "caption",
                                            wagtail.core.blocks.RichTextBlock(
                                                features=["bold", "italic", "link"],
                                                required=False,
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
                                wagtail.core.blocks.RichTextBlock(
                                    classname="footnotes",
                                    features=["ol", "ul", "bold", "italic", "link"],
                                ),
                            ),
                        ]
                    ),
                ),
                (
                    "authors",
                    wagtail.core.fields.StreamField(
                        [
                            (
                                "author",
                                wagtail.snippets.blocks.SnippetChooserBlock(
                                    mep.pages.models.Person
                                ),
                            )
                        ],
                        blank=True,
                        help_text="Select or create new people to add as authors.",
                    ),
                ),
                (
                    "editors",
                    wagtail.core.fields.StreamField(
                        [
                            (
                                "editor",
                                wagtail.snippets.blocks.SnippetChooserBlock(
                                    mep.pages.models.Person
                                ),
                            )
                        ],
                        blank=True,
                        help_text="Select or create new people to add as editors.",
                    ),
                ),
                (
                    "featured_image",
                    models.ForeignKey(
                        blank=True,
                        help_text="Preview image for landing page list (if supported) and social media.",
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
            bases=(mep.pages.models.RdfPageMixin, "wagtailcore.page", models.Model),
        ),
        migrations.CreateModel(
            name="Person",
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
                (
                    "name",
                    models.CharField(
                        help_text="Full name for the person as it should appear in the author list.",
                        max_length=255,
                    ),
                ),
                (
                    "url",
                    models.URLField(
                        blank=True,
                        default="",
                        help_text="Personal website, profile page, or social media profile pagefor this person.",
                    ),
                ),
                (
                    "twitter_id",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Twitter user ID. Note that this is NOT a username - you canfind yours at http://tweeterid.com/. Will not change if ausername changes.",
                        max_length=100,
                    ),
                ),
            ],
        ),
        migrations.RenameModel(
            old_name="LandingPage",
            new_name="ContentLandingPage",
        ),
        migrations.AddField(
            model_name="contentpage",
            name="authors",
            field=wagtail.core.fields.StreamField(
                [
                    (
                        "author",
                        wagtail.snippets.blocks.SnippetChooserBlock(
                            mep.pages.models.Person
                        ),
                    )
                ],
                blank=True,
                help_text="Select or create new people to add as authors.",
            ),
        ),
        migrations.AddField(
            model_name="contentpage",
            name="editors",
            field=wagtail.core.fields.StreamField(
                [
                    (
                        "editor",
                        wagtail.snippets.blocks.SnippetChooserBlock(
                            mep.pages.models.Person
                        ),
                    )
                ],
                blank=True,
                help_text="Select or create new people to add as editors.",
            ),
        ),
    ]
