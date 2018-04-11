# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-04 19:02
from __future__ import unicode_literals
from dateutil.relativedelta import relativedelta


from django.db import migrations


class Migration(migrations.Migration):

    def recalculate_durations(apps, schema_editor):
        '''
        Recalculate subscription durations based on duration in months
        for Subscriptions without end date.

        This migration is necessary because the migration in 0012_recalculate_durations
        did not account for Subscriptions that did not have end dates set but
        which did have durations, which had been entered into production prior
        to the data migation being run.

        The migration targets Subscription objects that have a start_date, lack
        an end date, and have a duration that is still reflecting months rather
        than the current unit of day for duration.
        '''

        Subscription = apps.get_model('accounts', 'Subscription')
        # - fetch subscriptiosn that meet the following criteria
        # 1) have a start_date
        # 2) lack an end_date
        # 3) have a duration set
        subs = Subscription.objects.filter(
            start_date__isnull=False,
            end_date__isnull=True,
            duration__isnull=False
        )

        for sub in subs:
            # Follow Beach's practice that a month carries over to the same day
            # on the next month via relativedelta of a month
            # Treating duration as months
            sub.end_date = sub.start_date + relativedelta(months=sub.duration)
            # Set duration using the delta between the newly calculated
            # end_date
            sub.duration = (sub.end_date - sub.start_date).days
            # save the new values
            sub.save()

    dependencies = [
        ('accounts', '0014_add_address_rel_to_person'),
    ]

    operations = [
        migrations.RunPython(recalculate_durations)
    ]
