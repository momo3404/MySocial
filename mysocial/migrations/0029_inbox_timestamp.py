# Generated by Django 4.2.9 on 2024-03-17 05:04

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mysocial', '0028_inbox'),
    ]

    operations = [
        migrations.AddField(
            model_name='inbox',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 3, 17, 5, 4, 14, 254400, tzinfo=datetime.timezone.utc)),
        ),
    ]