# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-05-07 17:01
from __future__ import unicode_literals

from django.contrib.auth.management import create_permissions
from django.db import migrations


new_content_editor_perms = [
    "add_creator",
    "change_creator",
    "delete_creator",
    "add_creatortype",
    "change_creatortype",
    "delete_creatortype",
]


def update_content_editor_group(apps, schema_editor):
    # adapted from 0002 content editor migration

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # make sure permissions are created before loading the fixture
    # which references them
    # (when running migrations all at once, permissions may not yet exist)
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    editor_group = Group.objects.get(name="Content Editor")
    permissions = []
    for codename in new_content_editor_perms:
        # using explicit get so that there will be an error if an
        # expected permission is not found
        permissions.append(Permission.objects.get(codename=codename))

    # add the new permissions without removing existing ones
    editor_group.permissions.add(*permissions)


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0003_content_editor_perms_location"),
        ("books", "0006_item_creators"),
    ]

    operations = [
        migrations.RunPython(
            update_content_editor_group, reverse_code=migrations.RunPython.noop
        ),
    ]
