# Generated by Django 4.1.13 on 2024-10-03 16:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("campaign", "0007_rename_summarization_promt_campaign_summarization_prompt"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="contact_list",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="campaigns",
                to="campaign.contactlist",
            ),
        ),
    ]
