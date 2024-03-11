# Generated by Django 4.2.9 on 2024-03-10 06:36

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('mysocial', '0018_alter_followrequest_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='follower',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True),
        ),
    ]
