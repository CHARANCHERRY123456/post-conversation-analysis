from django.contrib import admin
from django.urls import path
from .views import upload_json

urlpatterns = [
    path('conversation/', upload_json),
]