# finance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeeCollectionViewSet, FeeStructureViewSet

router = DefaultRouter()
router.register(r'collection', FeeCollectionViewSet, basename='fee-collection')
router.register(r'structure', FeeStructureViewSet, basename='fee-structure')

urlpatterns = [
   path('', include(router.urls)),
]
