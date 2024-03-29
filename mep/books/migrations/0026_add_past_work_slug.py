# Generated by Django 2.2.11 on 2020-07-07 16:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("books", "0025_populate_sort_title"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="edition",
            options={"ordering": ["date", "volume"]},
        ),
        migrations.AlterField(
            model_name="work",
            name="public_notes",
            field=models.TextField(
                blank=True,
                help_text="Notes for display on the public website.  Use markdown for formatting.",
            ),
        ),
        migrations.CreateModel(
            name="PastWorkSlug",
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
                    "slug",
                    models.SlugField(
                        help_text="Short, durable, unique identifier for use in URLs. Editing will change the public, citable URL for library books.",
                        max_length=100,
                        unique=True,
                    ),
                ),
                (
                    "work",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="past_slugs",
                        to="books.Work",
                    ),
                ),
            ],
        ),
    ]
