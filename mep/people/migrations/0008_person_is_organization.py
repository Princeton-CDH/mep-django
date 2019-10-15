# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-26 19:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0007_location_unique_constraints'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='is_organization',
            field=models.BooleanField(default=False, help_text='Mark as true to indicate this is an organization'),
        ),
    ]