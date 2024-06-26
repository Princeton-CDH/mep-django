# Generated by Django 3.2.20 on 2024-04-30 20:46

from django.db import migrations
from django.contrib.admin.models import CHANGE
from django.conf import settings
from viapy.api import ViafEntity


def populate_dates_from_viaf(apps, schema_editor):
    """Generate uniuqe slugs for people"""
    Person = apps.get_model("people", "Person")
    ContentType = apps.get_model("contenttypes", "ContentType")
    User = apps.get_model("auth", "User")
    LogEntry = apps.get_model("admin", "LogEntry")

    person_content_type = ContentType.objects.get(model="person", app_label="people")
    script_user = User.objects.get(username=settings.SCRIPT_USERNAME)

    # find all person records with viaf id set but unset birth year
    # NOTE: in migrations we can't use birth/death aliases for start/end yaer
    for p in Person.objects.exclude(viaf_id="").filter(start_year__isnull=True):
        # store values before populating
        birth, death = p.start_year, p.end_year
        # populate from viaf (requires remote request to load RDF)
        viaf_entity = ViafEntity(p.viaf_id.strip("/"))
        p.start_year = viaf_entity.birthyear
        p.end_year = viaf_entity.deathyear
        # if values have changed, save the record and create log entry
        if p.start_year != birth or p.end_year != death:
            p.save()

            LogEntry.objects.create(
                user_id=script_user.id,
                content_type_id=person_content_type.pk,
                object_id=p.pk,
                object_repr=f"Person pk={p.pk} {p.sort_name}",
                change_message="Update birth/death dates from VIAF",
                action_flag=CHANGE,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0021_allowing_null_in_country_code_and_geonames_id"),
        ("admin", "0003_logentry_add_action_flag_choices"),
        ("common", "0005_create_script_user"),
    ]

    operations = [
        migrations.RunPython(
            code=populate_dates_from_viaf,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
