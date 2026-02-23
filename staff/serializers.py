from rest_framework import serializers
from .models import StaffAttendance
from normaluser.models import NormalUser

class StaffMemberSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    custom_id = serializers.CharField(source='admin_custom_id', read_only=True)

    class Meta:
        model = NormalUser
        fields = ['id', 'full_name', 'custom_id', 'role']

class StaffAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffAttendance
        fields = '__all__'