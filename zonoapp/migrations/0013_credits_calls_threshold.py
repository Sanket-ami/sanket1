# Generated by Django 5.0.7 on 2024-11-12 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("zonoapp", "0012_delete_availablebalance_delete_creditrate"),
    ]

    operations = [
        migrations.AddField(
            model_name="credits",
            name="calls_threshold",
            field=models.IntegerField(default=3),
        ),
    ]