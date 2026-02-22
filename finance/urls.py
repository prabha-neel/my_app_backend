# finance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeeCollectionViewSet, FeeStructureViewSet, SalaryManagementViewSet

router = DefaultRouter()
router.register(r'collection', FeeCollectionViewSet, basename='fee-collection')
router.register(r'structure', FeeStructureViewSet, basename='fee-structure')
router.register(r'salaries', SalaryManagementViewSet, basename='salary-management')

urlpatterns = [
   path('', include(router.urls)),
]