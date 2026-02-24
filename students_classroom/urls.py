from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StandardViewSet,
    ClassroomSessionViewSet,
    JoinRequestViewSet,
    PendingRequestsView,   # 👈 Naya View (Flutter ke liye)
    HandleRequestView      # 👈 Naya View (Flutter ke liye)
)

app_name = 'students_classroom'

router = DefaultRouter(trailing_slash=True)
router.register(r'standards', StandardViewSet, basename='standard')
router.register(r'sessions', ClassroomSessionViewSet, basename='session')
router.register(r'join-requests', JoinRequestViewSet, basename='joinrequest')

urlpatterns = [
    # 1. PEHLE ROUTER: Taaki tere purane /sessions/, /standards/ sab sahi chalein
    path('', include(router.urls)),

    # 2. FLUTTER COMPATIBILITY: Ye tabhi chalenge jab router match nahi hoga
    # Flutter: /api/v1/classroom/join-requests/
    path('join-requests/', PendingRequestsView.as_view(), name='flutter-pending-requests'),
    
    # Flutter: /api/v1/classroom/sessions/<id>/approve-request/
    path('sessions/<str:session_id>/<str:action>-request/', HandleRequestView.as_view(), name='flutter-handle-request'),

    # 3. OTHER MANUAL PATHS
    path(
        'join-requests/my/', 
        JoinRequestViewSet.as_view({'get': 'list'}), 
        name='joinrequest-my-list'
    ),
]