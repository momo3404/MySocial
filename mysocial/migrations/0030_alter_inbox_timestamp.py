# Generated by Django 4.2.9 on 2024-03-17 16:02

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mysocial", "0029_inbox_timestamp"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inbox",
            name="timestamp",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2024, 3, 17, 16, 2, 28, 118073, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]