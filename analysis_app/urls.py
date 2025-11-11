
from django.urls import path
from .views import upload_json, analyse_chat, get_all_analyses

urlpatterns = [
    path('conversation/', upload_json),
    path("analysis/<int:conversation_id>/", analyse_chat, name="Gives a Conversation Analysis"),
    path('analyses/', get_all_analyses, name='get_all_analyses'),
]