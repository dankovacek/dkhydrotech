import io
from django.db import models
from django.utils import timezone
from django.conf import settings
from embed_video.fields import EmbedVideoField
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from PIL import Image
from io import BytesIO
import os.path
from mdeditor.fields import MDTextField

ENTRY_CHOICES = (
    ('project', 'PROJECT'),
)

class Entry(models.Model):
    """
    A generic Entry, covers all four categories: photo, video, illustration, blurb (writing).
    """
    id_prefix = 'ENTRY-'
    # models.DateField(default=timezone.now)
    created = models.DateTimeField(default=timezone.now)
    title = models.CharField(
        max_length=30, verbose_name="Title", blank=True, null=True)
    byline = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Title Byline")
    content = MDTextField()
    image = models.ImageField(blank=True, null=True, verbose_name="Main Image")
    img_thumb = models.ImageField(
        blank=True, null=True, upload_to=settings.MEDIA_URL, 
        editable=False, verbose_name="Image Thumbnail")
    video = EmbedVideoField(
        verbose_name="Video Link (optional)", blank=True, null=True)
    tags = models.CharField(max_length=500, blank=True,
                            null=True, verbose_name="Tags (comma separated)")
    post_type = models.CharField(
        max_length=7, choices=ENTRY_CHOICES, default='PROJECT')

    def save(self, *args, **kwargs):
        if not self.image.closed:
            if not self.make_thumbnail():
                raise Exception(
                    'Could not create thumbnail. .jpg, .jpeg, .gif, and .png are recognized types.')
        super(Entry, self).save(*args, **kwargs)


    def make_thumbnail(self):
        img = Image.open(self.image)
        width, height = img.size
        aspect = width / height
        thumb_width = 600
        thumb_height = thumb_width / aspect
        thumb_size = thumb_width, thumb_height

        img.thumbnail(thumb_size, Image.ANTIALIAS)
        thumb_name, thumb_extension = os.path.splitext(self.image.name)
        thumb_extension = thumb_extension.lower()
        thumb_filename = thumb_name + '_thumb' + thumb_extension

        if thumb_extension in ['.jpg', '.jpeg']:
            FTYPE = 'JPEG'
        elif thumb_extension == '.gif':
            FTYPE = 'GIF'
        elif thumb_extension == '.png':
            FTYPE = 'PNG'
        else:
            return False  # Unrecognized file type

        # Save thumbnail to in-memory file as StringIO
        temp_thumb = BytesIO()
        img.save(temp_thumb, FTYPE)
        temp_thumb.seek(0)

        # set save=False, otherwise it will run in an infinite loop
        self.img_thumb.save(thumb_filename, ContentFile(
            temp_thumb.read()), save=False)
        temp_thumb.close()

        return True

    def tags_as_list(self):
        tags = [e.strip().replace(' ', '_') for e in self.tags.split(',')]
        self.tags = ','.join(tags)
        self.save()
        return tags


SEARCH_DIST_CHOICES = (
    (5.0, '5km'),
    (10.0, '10km'),
    (25.0, '25km'),
    (50.0, '50km'),
)


class StationSearchTarget(models.Model):
    """
    A model instance to save search targets, which are comprised of
    lat/lon coordinates and a target radius.
    """
    id_prefix = 'TARGET-'
    # models.DateField(default=timezone.now)
    lat = models.DecimalField(
        max_digits=9, decimal_places=4, null=False, blank=False,
        verbose_name="Target Latitude [decimal degrees]",
        validators=[MinValueValidator(float(-80)), MaxValueValidator(int(84))])
    lon = models.DecimalField(
        max_digits=9, decimal_places=4, null=False, blank=False,
        verbose_name="Target Lontigude [decimal degrees]",
        validators=[MinValueValidator(int(-180)), MaxValueValidator(int(180))])
    search_radius = models.DecimalField(
        max_digits=3, decimal_places=1, choices=SEARCH_DIST_CHOICES,
        default='1km', null=False, blank=False, verbose_name="Search Radius [km]")


class ClimateStation(models.Model):
    """
    A model instance to manage station search results.
    """
    id_prefix = 'STN-'
    latlon = models.CharField(
        max_length=30, verbose_name="Lat/Lon [decimal degrees]",
        blank=True, null=True)

    start_year = models.CharField(
        max_length=30, verbose_name="Record Start Year", blank=True, null=True)

    end_year = models.CharField(
        max_length=30, verbose_name="Record End Year", blank=True, null=True)

    distance_to_target = models.CharField(
        max_length=30, verbose_name="Distance to Target [km]", blank=True, null=True)

    station_name = models.CharField(
        max_length=30, verbose_name="Station Name", blank=True, null=True)

    station_ID = models.CharField(
        max_length=30, verbose_name="Station ID", blank=True, null=True)

    new_file_name = models.CharField(
        max_length=30, verbose_name="File Name (for csv writing)", blank=True, null=True)


class Donation(models.Model):
    """
    A model instance to manage donations for tools used.
    """
    id_prefix = 'DON-'
    #email = EmailField(max_length=50, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(
        max_digits=9, decimal_places=2, null=False, blank=False,
        verbose_name="Donation Amount")
    tool_name = models.CharField(max_length=50)
    charge_id = models.CharField(max_length=234)
    currency = models.CharField(max_length=3)
    email = models.EmailField(max_length=254, blank=True, null=True)
