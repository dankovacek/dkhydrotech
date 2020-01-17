from django.urls import path

from . import views

app_name = 'bokeh_apps'

urlpatterns = [
    path('<app_ID>', views.BokehView.as_view(), name='bokeh_views'),
]