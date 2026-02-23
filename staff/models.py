from django.db import models
from django.conf import settings

class StaffAttendance(models.Model):
    ATTENDANCE_STATUS = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LEAVE', 'Leave'),
        ('HALF_DAY', 'Half Day'),
    ]

    organization = models.ForeignKey(
        'organizations.Organization', 
        on_delete=models.CASCADE, 
        related_name='staff_attendance_records'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='my_attendance'
    )
    date = models.DateField()
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='PRESENT')
    punch_in = models.TimeField(null=True, blank=True)
    punch_out = models.TimeField(null=True, blank=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='marked_attendances'
    )
    remark = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.date}"