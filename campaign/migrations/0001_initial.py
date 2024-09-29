# Generated by Django 5.0.7 on 2024-09-27 23:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("agent", "0001_initial"),
        ("provider", "0003_provider_provider_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="Campaign",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("campaign_name", models.CharField(max_length=255)),
                ("is_schedule", models.BooleanField(default=True)),
                ("organisation_name", models.CharField(max_length=255)),
                ("show_transcript", models.BooleanField(default=False)),
                ("process_type", models.CharField(max_length=255)),
                ("show_recording", models.BooleanField(default=True)),
                ("show_numbers", models.BooleanField(default=True)),
                ("create_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.CharField(default="SYSTEM", max_length=255, null=True),
                ),
                (
                    "modified_by",
                    models.CharField(default="SYSTEM", max_length=255, null=True),
                ),
                ("is_delete", models.BooleanField(default=False)),
                (
                    "agent",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="agent.agent",
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="provider.provider",
                    ),
                ),
            ],
        ),
    ]