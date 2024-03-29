# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-02 20:18
from __future__ import unicode_literals

from django.db import migrations
from django.conf import settings


def create_script_user(apps, schema_editor):
    # create a 'script' user so that import actions can be logged
    # via django log entry
    User = apps.get_model("auth", "User")
    User.objects.get_or_create(
        username=settings.SCRIPT_USERNAME, is_staff=False, is_active=False
    )


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0004_update_content_editor_perms_creatortype"),
    ]

    operations = [
        migrations.RunPython(
            create_script_user, reverse_code=migrations.RunPython.noop
        ),
    ]
