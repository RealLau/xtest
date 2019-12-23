# Generated by Django 2.2.4 on 2019-11-12 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xtests', '0010_reporttemplate'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bug_type', models.CharField(choices=[('1', 'Lowest'), ('2', 'Low'), ('3', 'Middle'), ('4', 'High'), ('5', 'Highest')], default='3', max_length=1)),
                ('bug_count', models.IntegerField()),
            ],
        ),
    ]
