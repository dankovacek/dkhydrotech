"""
URLS for portfolio App.
"""
from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static

from .views import EntryList, EntryCreate, EntryDetail, EntryUpdate, EntryDelete
from .views import PhotoList, DrawingList, VideoList, BlergList, TagList
from .views import DataVizDetail
from .views import ClimateScrapeCreate, ClimateScrapeResults, ClimateScrapeExport


urlpatterns = [
    url(r'^$', EntryList.as_view(), name="entry-list"),
    url(r'^markdownx/', include('markdownx.urls')),
    url(r'^create_entry$', EntryCreate.as_view(), name="entry-create"),
    url(r'^entry/(?P<pk>[0-9]+)$', EntryDetail.as_view(), name="entry-detail"),
    url(r'^entry/(?P<pk>[0-9]+)/update$',
        EntryUpdate.as_view(), name="entry-update"),
    url(r'^entry/(?P<pk>[0-9]+)/delete$',
        EntryDelete.as_view(), name="entry-delete"),
    url(r'^photos/$', PhotoList.as_view(), name="photo-list"),
    url(r'^videos/$', VideoList.as_view(), name="video-list"),
    url(r'^illustration/$', DrawingList.as_view(), name="drawing-list"),
    url(r'^rants/$', BlergList.as_view(), name="blerg-list"),
    url(r'^tags/(?P<pk>[a-zA-Z0-9_$&#()!@]+)$',
        TagList.as_view(), name="tag-list"),
    url(r'^dataviz/(?P<viz_url>[-\w]+)/$',
        DataVizDetail.as_view(), name="data-viz"),
    url(r'^tools/climate_data_finder/$',
        ClimateScrapeCreate.as_view(), name="climate-scrape"),
    url(r'^tools/climate_data_finder/results/(?P<pk>[0-9]+)$',
        ClimateScrapeResults.as_view(), name="climate-scrape-results"),
    url(r'^tools/climate_data_finder/output/(?P<station_ID>[0-9]+)/(?P<start_year>[0-9]+)/(?P<end_year>[0-9]+)$',
        ClimateScrapeExport, name="climate-scrape-export"),


]  # + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
