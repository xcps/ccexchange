# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-14 19:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('exchange', '0009_auto_20170914_1920'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chat',
            options={'ordering': ['-date']},
        ),
        migrations.AddField(
            model_name='chat',
            name='date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]