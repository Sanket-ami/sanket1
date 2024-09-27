# Generated by Django 5.0.7 on 2024-09-27 18:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("provider", "0001_initial"),
        ("voice", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="voice",
            name="voice_provider",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="provider.provider",
            ),
        ),
    ]
