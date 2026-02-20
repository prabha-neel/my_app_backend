from django.db import models
from organizations.models import Organization

class Vehicle(models.Model):
    FUEL_TYPES = [('Diesel', 'Diesel'), ('CNG', 'CNG'), ('Electric', 'Electric')]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_number = models.CharField(max_length=50, unique=True)
    vehicle_type = models.CharField(max_length=50, help_text="e.g. Bus, Van, Winger")
    capacity = models.PositiveIntegerField()
    driver_name = models.CharField(max_length=100)
    driver_contact = models.CharField(max_length=15)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES, default='Diesel')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.vehicle_number

class BusRoute(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='bus_routes')
    route_name = models.CharField(max_length=255)
    vehicle = models.OneToOneField(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='route')
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.route_name

class BusStop(models.Model):
    route = models.ForeignKey(BusRoute, on_delete=models.CASCADE, related_name='stops')
    stop_name = models.CharField(max_length=255)
    pickup_time = models.TimeField()
    drop_time = models.TimeField()
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']