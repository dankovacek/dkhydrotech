from django.contrib import admin

from mdeditor.widgets import MDEditorWidget

from embed_video.admin import AdminVideoMixin
from django.db import models
from .models import Entry


class MyModelAdmin(AdminVideoMixin, admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': MDEditorWidget}
    }


admin.site.register(Entry, MyModelAdmin)
