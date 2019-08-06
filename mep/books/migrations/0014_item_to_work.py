# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-08-06 15:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0013_item_ebook_url'),
        ('accounts', '0028_generic_event_partial_dates'),
    ]

    operations = [
        # rename item to work
        migrations.RenameModel('Item', 'Work'),
        # rename item.item_format to work.work_format
        migrations.RenameField('Work', 'item_format', 'work_format'),
        # rename item/work foreignkey on Creator
        migrations.RenameField('Creator', 'item', 'work'),
    ]
