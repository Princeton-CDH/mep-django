# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-12 19:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import mep.accounts.models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_account_card'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='end_date_precision',
            field=mep.accounts.models.DatePrecisionField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='purchase',
            name='start_date_precision',
            field=mep.accounts.models.DatePrecisionField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='card',
            field=models.ForeignKey(blank=True, help_text='Lending Library Card for this account', null=True, on_delete=django.db.models.deletion.SET_NULL, to='footnotes.Bibliography'),
        ),
    ]
