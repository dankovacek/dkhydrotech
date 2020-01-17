from django.urls import path

from . import views

app_name = 'bkapps'

urlpatterns = [
    path('flood_msmt', views.BokehView.as_view(), 
    name='bokeh-flood-msmt', kwargs={'app_ID': 'flood_msmt'}),
    path('sliders', views.BokehView.as_view(), 
    name='bokeh-sliders', kwargs={'app_ID': 'sliders'})
]