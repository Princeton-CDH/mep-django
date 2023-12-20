# Generated by Django 2.2.11 on 2020-03-12 19:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("footnotes", "0003_add_bibliography_manifest_and_footnote_canvas"),
    ]

    operations = [
        migrations.AlterField(
            model_name="footnote",
            name="content_type",
            field=models.ForeignKey(
                limit_choices_to=models.Q(
                    models.Q(
                        ("app_label", "people"),
                        ("model__in", ["country", "person", "address", "profession"]),
                    ),
                    models.Q(
                        ("app_label", "accounts"),
                        (
                            "model__in",
                            [
                                "account",
                                "event",
                                "subscription",
                                "borrow",
                                "reimbursement",
                                "purchase",
                            ],
                        ),
                    ),
                    models.Q(("app_label", "books"), ("model__in", ["item"])),
                    _connector="OR",
                ),
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.ContentType",
            ),
        ),
        migrations.AlterField(
            model_name="footnote",
            name="image",
            field=models.ForeignKey(
                blank=True,
                help_text="Image location from an imported manifest, if available.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="djiffy.Canvas",
            ),
        ),
    ]
