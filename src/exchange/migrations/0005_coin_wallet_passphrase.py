# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-12 19:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exchange', '0004_auto_20170911_2012'),
    ]

    operations = [
        migrations.AddField(
            model_name='coin',
            name='wallet_passphrase',
            field=models.CharField(blank=True, max_length=255, verbose_name='Wallet passphrase'),
        ),
    ]
