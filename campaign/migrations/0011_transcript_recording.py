# Generated by Django 5.1.2 on 2024-10-22 22:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaign', '0010_schedulecampaign'),
    ]

    operations = [
        migrations.AddField(
            model_name='transcript',
            name='recording',
            field=models.TextField(null=True),
        ),
    ]
