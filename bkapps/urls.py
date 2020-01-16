from django.urls import path

from . import views

app_name='sliders'

urlpatterns = [
    # path('', views.sliders, name='sliders'),
    path('<app_ID>', views.DataVizDetail.as_view(), name="dataviz-test"),
]