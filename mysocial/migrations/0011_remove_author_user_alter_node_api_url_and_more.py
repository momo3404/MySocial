# Generated by Django 4.2.9 on 2024-02-25 03:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mysocial', '0010_alter_followrequest_type_alter_post_type_comment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='author',
            name='user',
        ),
        migrations.AlterField(
            model_name='node',
            name='api_url',
            field=models.URLField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='node',
            name='host',
            field=models.CharField(default='127.0.0.1:8000', max_length=30),
        ),
    ]