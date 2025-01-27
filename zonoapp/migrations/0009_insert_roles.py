# Generated by Django 4.1.13 on 2024-10-07 20:04

from django.db import migrations

def insert_roles(apps, schema_editor):
    Role = apps.get_model('zonoapp', 'Role')
    roles = [
        {'role': 'Admin', 'is_deleted': False},
        {'role': 'QA', 'is_deleted': False},
        {'role': 'Caller', 'is_deleted': False},
    ]
    Role.objects.bulk_create([Role(**role) for role in roles])
class Migration(migrations.Migration):
    dependencies = [
        ("zonoapp", "0008_alter_paymentstatus_organisation_name"),
    ]

    operations = [
        migrations.RunPython(insert_roles),
    ]