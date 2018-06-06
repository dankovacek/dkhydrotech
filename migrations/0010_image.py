# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-17 18:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0009_entry_img_thumb'),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('image', models.ImageField(blank=True, null=True, upload_to='', verbose_name='Image')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='portfolio.Entry')),
            ],
        ),
    ]