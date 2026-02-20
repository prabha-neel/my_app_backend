from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeeCollectionViewSet

# 1. Router setup
router = DefaultRouter()

# 🎯 'fee' prefix se register kiya hai
# Iska matlab saare URLs /api/v1/finance/fee/ se shuru honge
router.register(r'fee', FeeCollectionViewSet, basename='fee-collection')

urlpatterns = [
    # 2. Router ke saare dynamic routes (collect, summary, etc.) include karo
    path('', include(router.urls)),
]