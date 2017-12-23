"""
URLS for dkht App.
"""
from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static

from .views import EntryList, EntryCreate, EntryDetail, EntryUpdate, EntryDelete
from .views import TagList, BlergList, Main
from .views import DataVizDetail
from .views import ClimateScrapeCreate, ClimateScrapeResults, ClimateScrapeExport


urlpatterns = [
    url('', Main.as_view(), name="main-view"),
    url('markdownx/', include('markdownx.urls')),
    url('create_entry/', EntryCreate.as_view(), name="entry-create"),
    url('entry/<int:pk>/', EntryDetail.as_view(), name="entry-detail"),
    url('entry/<int:pk>/update/',
        EntryUpdate.as_view(), name="entry-update"),
    url('entry/<int:pk>/delete/',
        EntryDelete.as_view(), name="entry-delete"),
    url('rants/', BlergList.as_view(), name="blerg-list"),
    url('tags/<int:pk>/',
        TagList.as_view(), name="tag-list"),
    url('dataviz/<viz_url>/',
        DataVizDetail.as_view(), name="data-viz"),
    url('tools/climate_data_finder/',
        ClimateScrapeCreate.as_view(), name="climate-scrape"),
    url('tools/climate_data_finder/results/<int:pk>/',
        ClimateScrapeResults.as_view(), name="climate-scrape-results"),
    url('tools/climate_data_finder/output/<station_ID>/<start_year>/<end_year>/',
        ClimateScrapeExport, name="climate-scrape-export"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
