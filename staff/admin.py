from django.contrib import admin
from .models import StaffAttendance

@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'date', 'status', 'punch_in', 'punch_out')
    list_filter = ('organization', 'date', 'status')
    search_fields = ('user__first_name', 'user__last_name', 'organization__name')