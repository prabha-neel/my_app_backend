from rest_framework import serializers
from .models import Notification
from django.utils.timesince import timesince

class NotificationSerializer(serializers.ModelSerializer):
    # Field name 'time' rakho kyunki frontend 'time' mang raha hai
    time = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'time']

    def get_time(self, obj):
        # Agar aaj ka hai to time, purana hai to '2 days ago'
        from django.utils import timezone
        if obj.created_at.date() == timezone.now().date():
            return obj.created_at.strftime("%I:%M %p") # 10:30 AM format
        return timesince(obj.created_at).split(',')[0] + " ago"