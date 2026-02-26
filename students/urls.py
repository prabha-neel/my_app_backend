from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudentViewSet, 
    SendParentRequestView, 
    StudentActionRequestView, 
    ParentDashboardView,
    AdminStudentSummaryView  # 👈 Ye import zaroori hai
)

router = DefaultRouter()
# Router ko khali string ('') ki jagah 'profile' ya kuch dena behtar hota hai, 
# par agar tune '' rakha hai toh hum summary path ko router se pehle likhenge.
router.register(r'', StudentViewSet, basename='student')

urlpatterns = [
    # 🚩 1. Summary API ko Router se PEHLE rakho taaki Django ise pehle pehchane
    path('summary/<int:student_id>/', AdminStudentSummaryView.as_view(), name='student-summary'),

    # 2. Baki paths
    path('parent/request/', SendParentRequestView.as_view(), name='send-parent-request'),
    path('parent/request/<int:pk>/action/', StudentActionRequestView.as_view(), name='parent-request-action'),
    path('dashboard/', ParentDashboardView.as_view(), name='parent-dashboard'),

    # 3. Router base path (Isse hamesha niche rakho agar ye empty string use kar raha hai)
    path('', include(router.urls)),
]