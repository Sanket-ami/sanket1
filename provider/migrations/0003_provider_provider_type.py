# Generated by Django 5.0.7 on 2024-09-27 22:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("provider", "0002_alter_provider_is_delete_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="provider",
            name="provider_type",
            field=models.CharField(default="dsfwe", max_length=255),
            preserve_default=False,
        ),
    ]
