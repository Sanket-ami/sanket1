# Generated by Django 5.0.7 on 2024-09-29 07:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaign', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='contact_list',
            field=models.JSONField(default=[]),
        ),
    ]
