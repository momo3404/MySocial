# Generated by Django 4.2.9 on 2024-03-11 02:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mysocial', '0022_post_likescount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='post',
            name='likesCount',
            field=models.IntegerField(default=0),
        ),
    ]