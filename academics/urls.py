from django.urls import path
from .views import MasterClassSetupView

urlpatterns = [
    path('master-setup/', MasterClassSetupView.as_view(), name='master-class-setup'),
]