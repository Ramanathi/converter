from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('download/<title>/', views.download_file),
]