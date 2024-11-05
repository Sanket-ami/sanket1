# Generated by Django 5.0.7 on 2024-10-30 22:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("zonoapp", "0010_availablebalance"),
    ]

    operations = [
        migrations.AddField(
            model_name="credits",
            name="balance",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name="credits",
            name="call_rate",
            field=models.DecimalField(
                decimal_places=2, default=10, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="credits",
            name="status_balance",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="credits",
            name="status_rate",
            field=models.DecimalField(
                decimal_places=2, default=10, max_digits=10, null=True
            ),
        ),
    ]