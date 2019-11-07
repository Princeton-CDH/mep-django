# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2019-11-07 20:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0007_content_page_creators'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoutableLandingPage',
            fields=[
                ('landingpage_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='pages.LandingPage')),
            ],
            options={
                'abstract': False,
            },
            bases=('pages.landingpage',),
        ),
    ]
