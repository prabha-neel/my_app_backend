from django.urls import path
from .views import (
   AddRouteToExistingVehicleView, VehicleListCreateView, VehicleDetailView,
   RouteListView, RouteDetailWithVehicleView
)

urlpatterns = [
   path('vehicles/', VehicleListCreateView.as_view(), name='vehicle-list'),
   path('vehicles/<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),
   path('add-route/', AddRouteToExistingVehicleView.as_view(), name='add-route-to-vehicle'),
   # Objective 3 Endpoints
   path('routes-list/', RouteListView.as_view(), name='route-list'),
   path('routes-list/<int:pk>/', RouteDetailWithVehicleView.as_view(), name='route-vehicle-detail'),
]
