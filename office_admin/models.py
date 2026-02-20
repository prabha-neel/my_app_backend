from django.db import models
from django.conf import settings
from organizations.models import Organization

# 📝 Notepad / Digital Notice Board
class SchoolNote(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed')]
    TYPE_CHOICES = [('NOTICE', 'General Notice'), ('MAINTENANCE', 'Maintenance'), ('URGENT', 'Urgent Alert')]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='office_notes')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    note_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='NOTICE')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

# 🏢 Asset Management (Fan, AC, Benches etc.)
class SchoolAsset(models.Model):
    CONDITION_CHOICES = [('GOOD', 'Working Fine'), ('REPAIR', 'Needs Maintenance'), ('BROKEN', 'Damaged')]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='school_assets')
    item_name = models.CharField(max_length=255) # Admin can type anything (Water Cooler etc.)
    category = models.CharField(max_length=50, default='OTHER') # Flexibility
    quantity = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=255, help_text="e.g. Room No 10, Hall")
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='GOOD')
    description = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)