# Generated by Django 2.0 on 2017-12-28 01:06

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dkht', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Donation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=9, verbose_name='Donation Amount')),
                ('tool_name', models.CharField(max_length=50)),
                ('charge_id', models.CharField(max_length=234)),
                ('currency', models.CharField(max_length=3)),
            ],
        ),
    ]
