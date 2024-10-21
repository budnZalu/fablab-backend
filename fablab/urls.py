from django.contrib import admin
from django.urls import path

from jobs import views

urlpatterns = [
    path('', views.index, name='index'),
    path('jobs/<int:pk>', views.job_detail, name='job'),
    path('printings/<int:pk>', views.printing_detail, name='printing'),
]
