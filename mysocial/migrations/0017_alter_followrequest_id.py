# Generated by Django 4.2.9 on 2024-03-10 06:03

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('mysocial', '0016_alter_followrequest_actor_alter_followrequest_object'),
    ]

    operations = [
        migrations.AlterField(
            model_name='followrequest',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True),
        ),
    ]