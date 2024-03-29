# Generated by Django 2.2.11 on 2020-04-22 17:56

from django.db import migrations

from mep.books.utils import generate_sort_title


def populate_sort_titles(apps, schema_editor):
    """populate sort titles for works"""
    Work = apps.get_model("books", "Work")

    works = Work.objects.all()
    for work in works:
        work.sort_title = generate_sort_title(work.title)
        work.save()


class Migration(migrations.Migration):
    dependencies = [
        ("books", "0024_add_work_sort_title"),
    ]

    operations = [
        migrations.RunPython(
            code=populate_sort_titles,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
