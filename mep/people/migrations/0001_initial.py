# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-05 16:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('code', models.CharField(blank=True, max_length=3)),
            ],
            options={
                'verbose_name_plural': 'countries',
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True)),
                ('start_year', models.PositiveIntegerField(blank=True, null=True)),
                ('end_year', models.PositiveIntegerField(blank=True, null=True)),
                ('mep_id', models.CharField(blank=True, max_length=255)),
                ('first_name', models.CharField(blank=True, max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('viaf_id', models.URLField(blank=True)),
                ('sex', models.CharField(blank=True, choices=[('', '----'), ('F', 'Female'), ('M', 'Male')], max_length=1)),
                ('title', models.CharField(blank=True, max_length=255)),
                ('nationalities', models.ManyToManyField(blank=True, to='people.Country')),
            ],
            options={
                'verbose_name_plural': 'people',
            },
        ),
        migrations.CreateModel(
            name='Profession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Relationship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_person', to='people.Person')),
            ],
        ),
        migrations.CreateModel(
            name='RelationshipType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='relationship',
            name='relationship_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.RelationshipType'),
        ),
        migrations.AddField(
            model_name='relationship',
            name='to_person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_person', to='people.Person'),
        ),
        migrations.AddField(
            model_name='person',
            name='profession',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='people.Profession'),
        ),
        migrations.AddField(
            model_name='person',
            name='relations',
            field=models.ManyToManyField(through='people.Relationship', to='people.Person'),
        ),
    ]
