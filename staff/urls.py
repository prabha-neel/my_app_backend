from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StaffAttendanceViewSet

router = DefaultRouter()
router.register(r'staff-attendance', StaffAttendanceViewSet, basename='staff-attendance')

urlpatterns = [
    path('', include(router.urls)),
]