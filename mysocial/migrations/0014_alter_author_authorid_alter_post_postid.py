# Generated by Django 4.2.9 on 2024-02-25 05:08

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('mysocial', '0013_remove_follower_attributes_follower_author_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='authorId',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='postId',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]