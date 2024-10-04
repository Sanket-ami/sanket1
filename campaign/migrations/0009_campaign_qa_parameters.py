# Generated by Django 4.1.13 on 2024-10-03 22:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("qa_parameters", "0003_qaparameters_parameters_name"),
        ("campaign", "0008_campaign_contact_list"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="qa_parameters",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="qa_parameters.qaparameters",
            ),
        ),
    ]