from rest_framework import serializers
from .models import Vehicle, BusRoute, BusStop

class BusStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusStop
        fields = ['id', 'stop_name', 'pickup_time', 'drop_time', 'order']

class BusRouteSerializer(serializers.ModelSerializer):
    stops = BusStopSerializer(many=True, required=False)

    class Meta:
        model = BusRoute
        fields = ['id', 'route_name', 'start_time', 'end_time', 'is_active', 'stops']

class VehicleSerializer(serializers.ModelSerializer):
    route = BusRouteSerializer(read_only=True)
    # Input ke liye route_data optional rakha hai
    route_data = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Vehicle
        fields = ['id', 'organization', 'vehicle_number', 'vehicle_type', 'capacity', 
                  'driver_name', 'driver_contact', 'fuel_type', 'is_active', 'route', 'route_data']

    def create(self, validated_data):
        route_data = validated_data.pop('route_data', None)
        vehicle = Vehicle.objects.create(**validated_data)
        return vehicle