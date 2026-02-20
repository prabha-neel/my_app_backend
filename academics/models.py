from django.db import models

# =============================================================================
# Models for Academics App
# =============================================================================

class Subject(models.Model):
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    is_custom = models.BooleanField(default=False)

    class Meta:
        unique_together = ('organization', 'name')

    def __str__(self):
        return self.name


class WeeklyTimetable(models.Model):
    DAY_CHOICES = [
        ('MON', 'Monday'), 
        ('TUE', 'Tuesday'), 
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'), 
        ('FRI', 'Friday'), 
        ('SAT', 'Saturday'),
    ]

    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    
    # 🔥 FIXED: Path changed from 'organizations.Standard' to 'students_classroom.Standard'
    standard = models.ForeignKey(
        'students_classroom.Standard', 
        on_delete=models.CASCADE, 
        related_name="timetable_entries"
    )
    
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    period_number = models.PositiveIntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE)

    class Meta:
        # standard ab students_classroom se aa raha hai, unique check wahi rahega
        unique_together = ('standard', 'day', 'period_number')

    def __str__(self):
        # standard.name tabhi chalega agar Standard model mein 'name' field hai
        return f"{self.standard} - {self.day} - P{self.period_number}"