# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-20 05:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0005_auto_20171020_0542'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entry',
            name='description',
        ),
        migrations.AddField(
            model_name='entry',
            name='byline',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Title Byline'),
        ),
        migrations.AddField(
            model_name='entry',
            name='text_body',
            field=models.TextField(blank=True, null=True, verbose_name='Body Text'),
        ),
        migrations.AlterField(
            model_name='entry',
            name='title',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='Title'),
        ),
    ]