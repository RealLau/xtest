# Generated by Django 2.2.4 on 2019-09-25 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xtests', '0003_auto_20190919_1645'),
    ]

    operations = [
        migrations.AlterField(
            model_name='caserecord',
            name='result_status',
            field=models.CharField(choices=[('P', 'Pass'), ('F', 'Fail'), ('B', 'Block'), ('Q', 'Pending')], default='Q', max_length=1),
        ),
    ]
