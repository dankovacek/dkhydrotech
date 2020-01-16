from django.urls import path

from . import views

app_name='sliders'

urlpatterns = [
    # path('', views.sliders, name='sliders'),
    path('<app_ID>', views.FloodMsmtErrorSimulator.as_view(), name="flood_msmt_err_sim"),
]