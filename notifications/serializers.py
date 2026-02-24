from rest_framework import serializers
from .models import Notification
from django.utils.timesince import timesince

class NotificationSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'created_at', 'time_ago']

    def get_time_ago(self, obj):
        return timesince(obj.created_at) + " ago"