from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Vehicle, BusRoute, BusStop
from .serializers import VehicleSerializer, BusRouteSerializer
from organizations.models import Organization

# Objective 1 & 2: List and Create Vehicle
class VehicleListCreateView(generics.ListCreateAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(organization__admin=self.request.user).select_related('route')

    def perform_create(self, serializer):
        with transaction.atomic():
            org_id = self.request.data.get('organization')
            org = get_object_or_404(Organization, id=org_id, admin=self.request.user)
            vehicle = serializer.save(organization=org)

            # Optional Route Creation
            route_data = self.request.data.get('route_data')
            if route_data:
                route = BusRoute.objects.create(
                    organization=org,
                    vehicle=vehicle,
                    route_name=route_data.get('route_name'),
                    start_time=route_data.get('start_time'),
                    end_time=route_data.get('end_time')
                )
                stops = route_data.get('stops', [])
                for idx, stop in enumerate(stops):
                    stop_data = stop.copy() # Ek copy banao taaki original data disturb na ho
                    stop_data.pop('order', None) # Agar JSON mein 'order' hai toh use hata do
                    BusStop.objects.create(route=route, order=idx+1, **stop_data)

class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(organization__admin=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        # Objective 2: Check if route exists, else frontend can show 'Add Route'
        if not instance.route if hasattr(instance, 'route') else True:
            data['message'] = "No route assigned. You can add a route now."
        return Response(data)

# Objective 3: Route List and Vehicle Details
class RouteListView(generics.ListAPIView):
    serializer_class = BusRouteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BusRoute.objects.filter(organization__admin=self.request.user)

class RouteDetailWithVehicleView(generics.RetrieveAPIView):
    serializer_class = BusRouteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BusRoute.objects.filter(organization__admin=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        # Vehicle ki details add karna
        if instance.vehicle:
            data['vehicle_details'] = {
                "number": instance.vehicle.vehicle_number,
                "driver": instance.vehicle.driver_name,
                "contact": instance.vehicle.driver_contact
            }
        return Response(data)