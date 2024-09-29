# Generated by Django 5.0.7 on 2024-09-27 23:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("provider", "0003_provider_provider_type"),
        ("voice", "0003_voice_created_by_voice_modified_by"),
    ]

    operations = [
        migrations.CreateModel(
            name="Agent",
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
                ("agent_name", models.CharField(max_length=255)),
                ("agent_configuration", models.JSONField()),
                ("agent_prompt", models.TextField(null=True)),
                ("organisation_name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.CharField(default="SYSTEM", max_length=255, null=True),
                ),
                (
                    "modified_by",
                    models.CharField(default="SYSTEM", max_length=255, null=True),
                ),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "agent_provider",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="provider.provider",
                    ),
                ),
                (
                    "voice",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="voice.voice",
                    ),
                ),
            ],
            options={
                "db_table": "agent",
            },
        ),
    ]