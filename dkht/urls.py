"""
URLS for dkht App.
"""
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from .views import EntryList, EntryCreate, EntryDetail, EntryUpdate, EntryDelete
from .views import TagList, BlergList, Main
from .views import DataVizDetail
from .views import ClimateScrapeCreate, ClimateScrapeResults, ClimateScrapeExport

app_name = 'dkht'

urlpatterns = [
    path('', Main.as_view(), name="main-view"),
    path('markdownx/', include('markdownx.urls')),
    path('create_entry/', EntryCreate.as_view(), name="entry-create"),
    path('entry/<int:pk>/', EntryDetail.as_view(), name="entry-detail"),
    path('entry/<int:pk>/update/',
         EntryUpdate.as_view(), name="entry-update"),
    path('entry/<int:pk>/delete/',
         EntryDelete.as_view(), name="entry-delete"),
    path('rants/', BlergList.as_view(), name="blerg-list"),
    path('tools/climate_data_finder/',
         ClimateScrapeCreate.as_view(), name="climate-scrape"),
    # url('dataviz/<viz_url>/',
    #     DataVizDetail.as_view(), name="data-viz"),
    # url('tags/<int:pk>/',
    #     TagList.as_view(), name="tag-list"),
    # url('tools/climate_data_finder/results/<int:pk>/',
    #     ClimateScrapeResults.as_view(), name="climate-scrape-results"),
    # url('tools/climate_data_finder/output/<station_ID>/<start_year>/<end_year>/',
    #     ClimateScrapeExport, name="climate-scrape-export"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
