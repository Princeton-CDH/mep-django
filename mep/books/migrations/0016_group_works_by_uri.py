# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-08-06 21:57
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import Count

from mep.books.migration_group_work_utils import merge_works, ok_to_merge


def group_works_by_uri(apps, schema_editor):
    # merge works based on URI, with sanity-checking on title & authors

    Work = apps.get_model('books', 'Work')
    # get a distinct list of all work URIs that appear more than once
    uris = Work.objects.exclude(uri='').values('uri') \
                       .annotate(Count('uri')) \
                       .filter(uri__count__gt=1) \
                       .order_by('-uri__count') \
                       .values_list('uri', flat=True)

    for uri in uris:
        # find all works with the URI
        works = Work.objects.filter(uri=uri)
        # if not ok to merge, do nothing
        if not ok_to_merge(works):
            continue

        merge_works(works, apps)
        # no logic to generate editions, since there is not
        # enough data in the database to support it


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0015_split_work_edition'),
        ('accounts', '0030_event_edition'),
    ]

    operations = [
        migrations.RunPython(group_works_by_uri,
                             reverse_code=migrations.RunPython.noop),
    ]