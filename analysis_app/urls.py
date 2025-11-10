from django.contrib import admin
from django.urls import path
from .views import upload_json , analyse_chat

urlpatterns = [
    path('conversation/', upload_json),
    path("analysis/<int:conversation_id>/" , analyse_chat , name="Gives a Conversation Analysis")
]