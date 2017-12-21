from django.contrib import admin

from embed_video.admin import AdminVideoMixin
from .models import Entry

class MyModelAdmin(AdminVideoMixin, admin.ModelAdmin):
    pass

admin.site.register(Entry, MyModelAdmin)
