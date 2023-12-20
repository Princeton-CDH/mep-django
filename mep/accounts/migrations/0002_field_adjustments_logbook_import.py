# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-25 13:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="account",
            options={"ordering": ("persons__sort_name",)},
        ),
        migrations.AlterModelOptions(
            name="accountaddress",
            options={"verbose_name": "Account-address association"},
        ),
        migrations.AlterField(
            model_name="reimbursement",
            name="price",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=8, null=True
            ),
        ),
        migrations.AlterField(
            model_name="subscribe",
            name="currency",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "----"),
                    ("USD", "US Dollar"),
                    ("FRF", "French Franc"),
                    ("GBP", "British Pound"),
                ],
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="subscribe",
            name="duration",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Duration in months. Weeks may be noted with fractions in decimal form.",
                max_digits=4,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="subscribe",
            name="modification",
            field=models.CharField(
                blank=True,
                choices=[("", "----"), ("sup", "Supplement"), ("ren", "Renewal")],
                help_text="Use to indicate supplement or renewal.",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="subscribe",
            name="price_paid",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AlterField(
            model_name="subscribe",
            name="sub_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("A", "A"),
                    ("B", "B"),
                    ("A+B", "A+B"),
                    ("AdL", "AdL"),
                    ("Stu", "Student"),
                    ("Prof", "Professor"),
                    ("Oth", "Other"),
                ],
                max_length=255,
                verbose_name="type",
            ),
        ),
        migrations.AlterField(
            model_name="subscribe",
            name="volumes",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Number of volumes for checkout",
                max_digits=4,
                null=True,
            ),
        ),
    ]
