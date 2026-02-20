from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, SendParentRequestView, StudentActionRequestView, ParentDashboardView

router = DefaultRouter()
router.register(r'', StudentViewSet, basename='student')

urlpatterns = [
    path('', include(router.urls)),

    # Normal user yahan bache ka username post karega
    path('parent/request/', SendParentRequestView.as_view(), name='send-parent-request'),
    
    # Student yahan se accept/reject karega (id = Connection ID)
    path('parent/request/<int:pk>/action/', StudentActionRequestView.as_view(), name='parent-request-action'),
    path('dashboard/', ParentDashboardView.as_view(), name='parent-dashboard'),
]