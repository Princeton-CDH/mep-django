# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-28 14:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import mep.accounts.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('people', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='AccountAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True)),
                ('address_line_1', models.CharField(blank=True, max_length=255)),
                ('address_line_2', models.CharField(blank=True, max_length=255)),
                ('city_town', models.CharField(max_length=255)),
                ('postal_code', models.CharField(blank=True, max_length=25)),
                ('latitude', models.DecimalField(blank=True, decimal_places=5, max_digits=8, null=True, validators=[mep.accounts.models.verify_latlon])),
                ('longitude', models.DecimalField(blank=True, decimal_places=5, max_digits=8, null=True, validators=[mep.accounts.models.verify_latlon])),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Country')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='accountaddress',
            name='address',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Address'),
        ),
        migrations.AddField(
            model_name='accountaddress',
            name='care_of_person',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='people.Person'),
        ),
        migrations.AddField(
            model_name='account',
            name='addresses',
            field=models.ManyToManyField(blank=True, through='accounts.AccountAddress', to='accounts.Address'),
        ),
        migrations.AddField(
            model_name='account',
            name='persons',
            field=models.ManyToManyField(blank=True, to='people.Person'),
        ),
    ]
