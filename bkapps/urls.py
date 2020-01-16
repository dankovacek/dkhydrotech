from django.urls import path

from . import views

app_name='bokeh_apps'

urlpatterns = [
    # path('', views.sliders, name='sliders'),
    path('flood_msmt_error_simulator', views.FloodMsmtErrorSimulator.as_view(), name="flood_msmt_err_sim"),
]