# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-17 22:30
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0014_auto_20171117_2203'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entryimage',
            name='post',
        ),
        migrations.DeleteModel(
            name='EntryImage',
        ),
    ]