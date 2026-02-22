# teachers/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeacherViewSet, MySalaryView

router = DefaultRouter()
router.register(r'my-salaries', MySalaryView, basename='my-salary') 
router.register(r'', TeacherViewSet, basename='teacher') 

urlpatterns = [
    path('', include(router.urls)),
]