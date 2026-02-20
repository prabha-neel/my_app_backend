from django.urls import path
from .views import SchoolNoteListCreateView, SchoolAssetListCreateView

urlpatterns = [
    path('notes/', SchoolNoteListCreateView.as_view(), name='note-list-create'),
    path('assets/', SchoolAssetListCreateView.as_view(), name='asset-list-create'),
]