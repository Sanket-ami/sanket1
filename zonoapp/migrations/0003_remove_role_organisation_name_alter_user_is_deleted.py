# Generated by Django 5.1.1 on 2024-10-11 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zonoapp', '0002_notification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='role',
            name='organisation_name',
        ),
        migrations.AlterField(
            model_name='user',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
