# Generated by Django 2.0 on 2017-12-21 23:21

from django.db import migrations, models
import django.utils.timezone
import embed_video.fields
import markdownx.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ClimateStation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latlon', models.CharField(blank=True, max_length=30, null=True, verbose_name='Lat/Lon [decimal degrees]')),
                ('start_year', models.CharField(blank=True, max_length=30, null=True, verbose_name='Record Start Year')),
                ('end_year', models.CharField(blank=True, max_length=30, null=True, verbose_name='Record End Year')),
                ('distance_to_target', models.CharField(blank=True, max_length=30, null=True, verbose_name='Distance to Target [km]')),
                ('station_name', models.CharField(blank=True, max_length=30, null=True, verbose_name='Station Name')),
                ('station_ID', models.CharField(blank=True, max_length=30, null=True, verbose_name='Station ID')),
                ('new_file_name', models.CharField(blank=True, max_length=30, null=True, verbose_name='File Name (for csv writing)')),
            ],
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('title', models.CharField(blank=True, max_length=30, null=True, verbose_name='Title')),
                ('byline', models.CharField(blank=True, max_length=100, null=True, verbose_name='Title Byline')),
                ('text_body', markdownx.models.MarkdownxField(blank=True, null=True, verbose_name='Body Text')),
                ('image', models.ImageField(blank=True, null=True, upload_to='', verbose_name='Main Image')),
                ('img_thumb', models.ImageField(blank=True, editable=False, null=True, upload_to='thumbs', verbose_name='Image Thumbnail')),
                ('video', embed_video.fields.EmbedVideoField(blank=True, null=True, verbose_name='Video Link (optional)')),
                ('tags', models.CharField(blank=True, max_length=500, null=True, verbose_name='Tags (comma separated)')),
                ('type', models.CharField(choices=[('photo', 'PHOTO'), ('drawing', 'DRAWING'), ('video', 'VIDEO'), ('post', 'POST')], default='POST', max_length=7)),
            ],
        ),
        migrations.CreateModel(
            name='StationSearchTarget',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lat', models.DecimalField(decimal_places=4, max_digits=9, verbose_name='Target Latitude [decimal degrees]')),
                ('lon', models.DecimalField(decimal_places=4, max_digits=9, verbose_name='Target Lontigude [decimal degrees]')),
                ('search_radius', models.DecimalField(choices=[(5.0, '5km'), (10.0, '10km'), (20.0, '20km'), (40.0, '40km')], decimal_places=1, default='1km', max_digits=3, verbose_name='Search Radius [km]')),
            ],
        ),
    ]