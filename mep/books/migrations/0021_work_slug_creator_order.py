# Generated by Django 2.2.11 on 2020-04-01 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0020_format_on_delete'),
    ]

    operations = [
        migrations.AddField(
            model_name='creator',
            name='order',
            field=models.PositiveSmallIntegerField(blank=True, help_text='Order for multiple creators of the same type (optional)', null=True),
        ),
        migrations.AlterModelOptions(
            name='creator',
            options={'ordering': ['creator_type', 'order', 'person__sort_name']},
        ),
        migrations.AddField(
            model_name='work',
            name='slug',
            # not unique until slugs are generated
            field=models.SlugField(blank=True, help_text='Short, durable, unique identifier for use in URLs. Save and continue editing to have a new slug autogenerated.Editing will change the public, citable URL for books.', max_length=255),
        ),
    ]