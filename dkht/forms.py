from django import forms
from django.utils import timezone
from .models import Entry, StationSearchTarget  # , EntryImage


class EntryForm(forms.ModelForm):

    def save(self, commit=True):
        self.instance.entry = self.entry
        return super().save(commit)

    class Meta:
        model = Entry
        fields = ('type', 'title', 'byline',
                  'text_body', 'image', 'tags', 'video')

    def __init__(self, *args, **kwargs):
        # Call to ModelForm constructor
        super(EntryForm, self).__init__(*args, **kwargs)
        self.fields['text_body'].widget.attrs['height'] = '50vh'


class ClimateScrapeForm(forms.ModelForm):

    # def save(self, commit=True):
    #     self.instance. = self.ent

    class Meta:
        model = StationSearchTarget
        fields = ('lat', 'lon', 'search_radius')

    def __init__(self, *args, **kwargs):
        # Call to ModelForm constructor
        super(ClimateScrapeForm, self).__init__(*args, **kwargs)
        self.fields['lat'].widget.attrs['width'] = '200px'
        self.fields['lon'].widget.attrs['width'] = '200px'
        self.fields['search_radius'].widget.attrs['width'] = '200px'

    # def __init__(self, *args, **kwargs):
    #     # Call to ModelForm constructor
    #     super(ClimateScrapeForm, self).__init__(*args, **kwargs)
    #

#
# class EntryImageForm(forms.ModelForm):
#
#     def save(self, commit=True):
#         self.instance.entryimage = self.entry
#         return super().save(commit)
#
#
#     class Meta:
#         model = EntryImage
#         fields = ('image',)
