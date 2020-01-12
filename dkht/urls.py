"""
URLS for dkht App.
"""
from django.conf.urls import include, url
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import EntryList, EntryCreate, EntryDetail, EntryUpdate, EntryDelete
from .views import TagList, Main, Contact
from .views import PaymentSuccess
from .views import ClimateScrapeCreate, ClimateScrapeResults, ClimateScrapeExport, ClimateScrapeAnnualMaxPrecip

from .stripe_payment import DonateCheckout

from markdownx import urls as markdownx

app_name = 'dkht'

urlpatterns = [
    path('', Main.as_view(), name="main-view"),
    path('contact/', Contact.as_view(), name="contact-view"),
    path('markdownx/', include(markdownx)),
    path('projects/', EntryList.as_view(), name="entry-list"),
    path('create_entry/', EntryCreate.as_view(), name="entry-create"),
    path('entry/<int:pk>/', EntryDetail.as_view(), name="entry-detail"),
    path('entry/<int:pk>/update/',
         EntryUpdate.as_view(), name="entry-update"),
    path('entry/<int:pk>/delete/',
         EntryDelete.as_view(), name="entry-delete"),
    path('tags/<pk>',
         TagList.as_view(), name="tag-list"),
    path('tools/climate_data_finder/',
         ClimateScrapeCreate.as_view(), name="climate-scrape"),
    path('tools/climate_data_finder/results/<pk>/',
         ClimateScrapeResults.as_view(), name="climate-scrape-results"),
    path('tools/climate_data_finder/output/<station_ID>/<start_year>/<end_year>/',
         ClimateScrapeExport, name="climate-scrape-export"),
    path('tools/climate_data_finder/output/max/<station_ID>/<start_year>/<end_year>/',
         ClimateScrapeAnnualMaxPrecip, name="climate-scrape-annual-max-precip"),
    path('donation-checkout/', DonateCheckout, name="donate-checkout"),
    path('payment-success/<pk>/', PaymentSuccess.as_view(), name="payment-success"),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT) + \
        static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
