# Generated by Django 2.2.11 on 2020-04-28 13:56

from django.db import migrations, models
import mep.accounts.partial_date


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0031_on_delete"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="purchase_date",
            field=models.DateField(
                blank=True, help_text="Date the subscription was purchased.", null=True
            ),
        ),
        migrations.AddField(
            model_name="subscription",
            name="purchase_date_precision",
            field=mep.accounts.partial_date.DatePrecisionField(blank=True, null=True),
        ),
    ]
