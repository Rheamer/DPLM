# Generated by Django 4.0.1 on 2022-01-13 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devs', '0002_device_delete_page'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='uid',
        ),
        migrations.AddField(
            model_name='device',
            name='clientID',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='device',
            name='local_address',
            field=models.CharField(default='127.0.0.1', max_length=40),
        ),
        migrations.AddField(
            model_name='device',
            name='user',
            field=models.CharField(default='', max_length=100),
        ),
    ]