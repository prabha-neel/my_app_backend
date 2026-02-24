from rest_framework import serializers
from .models import Notification
from django.utils.timesince import timesince
from django.utils import timezone

class NotificationSerializer(serializers.ModelSerializer):
    # Field name 'time' rakho kyunki frontend 'time' mang raha hai
    time = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        # organization aur global_notification bhi add kar diye hain safety ke liye
        fields = [
            'id', 'title', 'message', 'notification_type', 
            'is_read', 'time', 'organization', 'global_notification'
        ]

    def get_time(self, obj):
        # 🎯 Aaj ka hai toh "10:30 AM", purana hai toh "2 days ago"
        now = timezone.now()
        if obj.created_at.date() == now.date():
            return obj.created_at.strftime("%I:%M %p")
        
        # timesince logic for older notifications
        return timesince(obj.created_at, now).split(',')[0] + " ago"