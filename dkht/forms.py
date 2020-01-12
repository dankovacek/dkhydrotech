from django import forms
from django.utils import timezone
from .models import Entry, StationSearchTarget, Donation 


class EntryForm(forms.ModelForm):

    def save(self, commit=True):
        self.instance.entry = self.entry

        return super().save(commit)

    class Meta:
        model = Entry
        fields = ('post_type', 'title', 'byline',
                  'content', 'image', 'tags', 'video')


class ClimateScrapeForm(forms.ModelForm):

    def save(self, commit=True):
        self.instance.stationsearchtarget = self.stationsearchtarget
        return super().save(commit)

    class Meta:
        model = StationSearchTarget
        fields = ['lat', 'lon', 'search_radius']

    def __init__(self, *args, **kwargs):
        # Call to ModelForm constructor
        super(ClimateScrapeForm, self).__init__(*args, **kwargs)
