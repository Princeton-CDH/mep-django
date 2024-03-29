# Generated by Django 2.2.11 on 2020-03-31 19:41

from django.db import migrations, models

# default ordering for some common creator types
CREATOR_TYPE_ORDER = {
    "Author": 1,
    "Editor": 2,
    "Illustrator": 3,
    "Introduction": 4,
    "Preface": 5,
    "Translator": 6,
}


def set_default_creator_type_ordering(apps, _schema_editor):
    """Set sensible order values for some pre-existing creator types."""

    CreatorType = apps.get_model("books", "CreatorType")
    for creator_type in CreatorType.objects.all():
        if creator_type.name in CREATOR_TYPE_ORDER:
            creator_type.order = CREATOR_TYPE_ORDER[creator_type.name]
            creator_type.save()


def reset_creator_type_ordering(apps, _schema_editor):
    """Reset all creator type order values to default."""

    CreatorType = apps.get_model("books", "CreatorType")
    for creator_type in CreatorType.objects.all():
        creator_type.order = 20
        creator_type.save()


class Migration(migrations.Migration):
    dependencies = [
        ("books", "0020_format_on_delete"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="creator",
            options={"ordering": ["creator_type__order", "creator__person__sort_name"]},
        ),
        migrations.AddField(
            model_name="creatortype",
            name="order",
            field=models.PositiveSmallIntegerField(
                default=20, help_text="order in which creators will be listed"
            ),
            preserve_default=False,
        ),
        migrations.RunPython(
            set_default_creator_type_ordering, reverse_code=reset_creator_type_ordering
        ),
    ]
