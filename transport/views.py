from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Vehicle, BusRoute, BusStop
from .serializers import VehicleSerializer, BusRouteSerializer
from organizations.models import Organization


from rest_framework.views import APIView

class AddRouteToExistingVehicleView(APIView):
   """
   🎯 Purpose: Pehle se bane hue Vehicle ke liye Route aur Stops create karna.
   """
   @transaction.atomic
   def post(self, request):
       # 1. IDs aur Data nikalna
       org_id = request.headers.get('School-ID') or request.data.get('organization')
       vehicle_id = request.data.get('vehicle_id') # Jis gaadi ke liye route bana rahe ho
       route_data = request.data.get('route_data')

       if not vehicle_id or not route_data:
           return Response({"error": "Bhai, 'vehicle_id' aur 'route_data' dono bhejo!"}, status=400)

       # 2. Validation: Kya school aur vehicle sahi hain?
       org = get_object_or_404(Organization, id=org_id, admin=request.user)
       vehicle = get_object_or_404(Vehicle, id=vehicle_id, organization=org)

       # 3. Check: Kya is gaadi ka pehle se koi route hai? (Duplicate se bachne ke liye)
       if BusRoute.objects.filter(vehicle=vehicle).exists():
           return Response({"error": "Bhai, is vehicle ka route pehle hi bana hua hai!"}, status=400)

       # 4. BusRoute Create Karo (As per your Screenshot)
       route = BusRoute.objects.create(
           organization=org,
           vehicle=vehicle,
           route_name=route_data.get('route_name'),
           start_time=route_data.get('start_time'),
           end_time=route_data.get('end_time'),
           is_active=True
       )

       # 5. BusStops Create Karo (Using keys from your image: pickup_time, drop_time)
       stops_list = route_data.get('stops', [])
       for idx, stop in enumerate(stops_list):
           BusStop.objects.create(
               route=route,
               stop_name=stop.get('stop_name'),
               pickup_time=stop.get('pickup_time'),
               drop_time=stop.get('drop_time'),
               order=idx + 1  # Automatic order handle kar rahe hain
           )

       return Response({
           "status": "success",
           "message": f"Route '{route.route_name}' added to vehicle {vehicle.vehicle_number}",
           "route_id": route.id
       }, status=status.HTTP_201_CREATED)




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
       # 🛡️ Yahan filter ko flexible karo taaki 404 na aaye
       user = self.request.user
       if hasattr(user, 'school_admin_profile'):
           org_ids = user.school_admin_profile.values_list('organization_id', flat=True)
           return Vehicle.objects.filter(organization_id__in=org_ids)
       # Agar purana logic 'admin' field use kar raha hai toh fallback:
       return Vehicle.objects.filter(organization__admin=user)

   def retrieve(self, request, *args, **kwargs):
       instance = self.get_object()
       serializer = self.get_serializer(instance)
      
       # 🎯 Jo tune manga: Detail + Route Info
       data = serializer.data
      
       # Agar route null hai (jo ki naye vehicle par hoga hi)
       if not instance.route if hasattr(instance, 'route') else True:
           data['route'] = None  # Frontend ko null milega
           data['action_required'] = "ADD_ROUTE"
           data['message'] = "Bhai, gaadi toh aa gayi par rasta (route) abhi set nahi hai. Add Route par click karo!"
      
       # Response 200 OK ke saath jayega (Django default for retrieve)
       # Agar tujhe strictly 201 chahiye toh status bhej sakte ho, par 200 standard hai GET ke liye.
       return Response(data, status=status.HTTP_200_OK)

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


# from rest_framework import generics, status
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.shortcuts import get_object_or_404
# from django.db import transaction
# from .models import Vehicle, BusRoute, BusStop
# from .serializers import VehicleSerializer, BusRouteSerializer
# from organizations.models import Organization

# # Objective 1 & 2: List and Create Vehicle
# class VehicleListCreateView(generics.ListCreateAPIView):
#     serializer_class = VehicleSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Vehicle.objects.filter(organization__admin=self.request.user).select_related('route')

#     def perform_create(self, serializer):
#         with transaction.atomic():
#             org_id = self.request.data.get('organization')
#             org = get_object_or_404(Organization, id=org_id, admin=self.request.user)
#             vehicle = serializer.save(organization=org)

#             # Optional Route Creation
#             route_data = self.request.data.get('route_data')
#             if route_data:
#                 route = BusRoute.objects.create(
#                     organization=org,
#                     vehicle=vehicle,
#                     route_name=route_data.get('route_name'),
#                     start_time=route_data.get('start_time'),
#                     end_time=route_data.get('end_time')
#                 )
#                 stops = route_data.get('stops', [])
#                 for idx, stop in enumerate(stops):
#                     stop_data = stop.copy() # Ek copy banao taaki original data disturb na ho
#                     stop_data.pop('order', None) # Agar JSON mein 'order' hai toh use hata do
#                     BusStop.objects.create(route=route, order=idx+1, **stop_data)

# class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = VehicleSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         # 🛡️ Yahan filter ko flexible karo taaki 404 na aaye
#         user = self.request.user
#         if hasattr(user, 'school_admin_profile'):
#             org_ids = user.school_admin_profile.values_list('organization_id', flat=True)
#             return Vehicle.objects.filter(organization_id__in=org_ids)
#         # Agar purana logic 'admin' field use kar raha hai toh fallback:
#         return Vehicle.objects.filter(organization__admin=user)

#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
        
#         # 🎯 Jo tune manga: Detail + Route Info
#         data = serializer.data
        
#         # Agar route null hai (jo ki naye vehicle par hoga hi)
#         if not instance.route if hasattr(instance, 'route') else True:
#             data['route'] = None  # Frontend ko null milega
#             data['action_required'] = "ADD_ROUTE"
#             data['message'] = "Bhai, gaadi toh aa gayi par rasta (route) abhi set nahi hai. Add Route par click karo!"
        
#         # Response 200 OK ke saath jayega (Django default for retrieve)
#         # Agar tujhe strictly 201 chahiye toh status bhej sakte ho, par 200 standard hai GET ke liye.
#         return Response(data, status=status.HTTP_200_OK)

# # Objective 3: Route List and Vehicle Details
# class RouteListView(generics.ListAPIView):
#     serializer_class = BusRouteSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return BusRoute.objects.filter(organization__admin=self.request.user)

# class RouteDetailWithVehicleView(generics.RetrieveAPIView):
#     serializer_class = BusRouteSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return BusRoute.objects.filter(organization__admin=self.request.user)

#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         data = serializer.data
#         # Vehicle ki details add karna
#         if instance.vehicle:
#             data['vehicle_details'] = {
#                 "number": instance.vehicle.vehicle_number,
#                 "driver": instance.vehicle.driver_name,
#                 "contact": instance.vehicle.driver_contact
#             }
#         return Response(data)