# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-10 14:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exchange', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalRate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.FloatField(verbose_name='Rate')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Date')),
                ('source', models.CharField(max_length=20, verbose_name='Source')),
                ('pair', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exchange.Pair', verbose_name='Pair')),
            ],
        ),
    ]