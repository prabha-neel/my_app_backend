from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, SchoolAdminViewSet, AdminDashboardAPIView # 👈 Import dashboard view

app_name = 'organizations'

router = DefaultRouter()
router.register(r'admins', SchoolAdminViewSet, basename='admin-profile')
router.register(r'', OrganizationViewSet, basename='organization-detail')

urlpatterns = [
    # 🚩 Dashboard API (Router se pehle rakho)
    path('dashboard/summary/', AdminDashboardAPIView.as_view(), name='admin-dashboard'),
    
    path('', include(router.urls)),
]