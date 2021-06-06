from django.urls import path

from . import views

app_name = 'bkapps'

urlpatterns = [
    path('flood_msmt', views.BokehView.as_view(), 
    name='bokeh-flood-msmt', kwargs={'app_ID': 'flood_msmt'}),
    path('ndimensions', views.BokehView.as_view(),
    name='ndimensions', kwargs={'app_ID': 'ndimensions'}),
    path('recognition_heuristic', views.BokehView.as_view(), 
    name='recognition-heuristic', kwargs={'app_ID': 'recognition_heuristic'}),
    path('sliders', views.BokehView.as_view(), 
    name='bokeh-sliders', kwargs={'app_ID': 'sliders'}),
]
