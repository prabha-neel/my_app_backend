from rest_framework import serializers
from .models import WeeklyTimetable, Subject
# Note: Source mapping ensures frontend sees 'School-ID' while backend uses 'organization_id'

class TimetablePeriodSerializer(serializers.Serializer):
    period_number = serializers.IntegerField(min_value=1)
    subject_name = serializers.CharField(max_length=100)
    teacher_id = serializers.UUIDField()

class SectionSetupSerializer(serializers.Serializer):
    standard_id = serializers.UUIDField()
    class_teacher_id = serializers.UUIDField(required=False, allow_null=True)
    days = serializers.ListField(child=serializers.ChoiceField(choices=WeeklyTimetable.DAY_CHOICES))
    periods = TimetablePeriodSerializer(many=True)

class MasterBulkSetupSerializer(serializers.Serializer):
    # 🔥 FIX: Frontend sends 'School-ID', it maps to 'organization_id' in validated_data
    organization_id = serializers.UUIDField(source='School-ID') 
    sections_data = SectionSetupSerializer(many=True)

    def to_representation(self, instance):
        """Response mein bhi 'School-ID' hi wapas bhejega"""
        rep = super().to_representation(instance)
        if 'organization_id' in rep:
            rep['School-ID'] = rep.pop('organization_id')
        return rep