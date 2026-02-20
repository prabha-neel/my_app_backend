from rest_framework import serializers
from .models import WeeklyTimetable
from organizations.models import Organization
from teachers.models import Teacher
from students_classroom.models import Standard

class TimetablePeriodSerializer(serializers.Serializer):
    period_number = serializers.IntegerField(min_value=1)
    subject_name = serializers.CharField(max_length=100)
    teacher_id = serializers.UUIDField() # Teacher ki Profile ID

class SectionSetupSerializer(serializers.Serializer):
    standard_id = serializers.UUIDField() # 1A, 1B etc.
    class_teacher_id = serializers.UUIDField(required=False)
    days = serializers.ListField(child=serializers.ChoiceField(choices=WeeklyTimetable.DAY_CHOICES))
    periods = TimetablePeriodSerializer(many=True)

class MasterBulkSetupSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()
    sections_data = SectionSetupSerializer(many=True)