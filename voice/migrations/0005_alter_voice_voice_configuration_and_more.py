# Generated by Django 5.0.7 on 2024-09-30 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("voice", "0004_voice_voice_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="voice",
            name="voice_configuration",
            field=models.JSONField(),
        ),
        migrations.AlterField(
            model_name="voice",
            name="voice_name",
            field=models.CharField(max_length=255, null=True),
        ),
    ]
