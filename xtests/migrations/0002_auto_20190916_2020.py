# Generated by Django 2.2.4 on 2019-09-16 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xtests', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testplan',
            name='end_time',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='testplan',
            name='start_time',
            field=models.DateTimeField(),
        ),
    ]
