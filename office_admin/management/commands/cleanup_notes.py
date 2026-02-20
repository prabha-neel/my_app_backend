from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from office_admin.models import SchoolNote

class Command(BaseCommand):
    help = '45 din se purane COMPLETED notes ko delete karne ke liye'

    def handle(self, *args, **kwargs):
        # 45 din ka buffer time
        cutoff_date = timezone.now() - timedelta(days=45)
        
        # Logic: 
        # 1. Sirf 'COMPLETED' status wale pakdo
        # 2. Jo 45 din se pehle update hue the (purane ho chuke hain)
        notes_to_delete = SchoolNote.objects.filter(
            status='COMPLETED',
            updated_at__lt=cutoff_date
        )
        
        count = notes_to_delete.count()
        notes_to_delete.delete()

        # Jo 'PENDING' ya 'IN_PROGRESS' hain, wo delete nahi honge chahe kitne bhi purane ho jayein
        self.stdout.write(self.style.SUCCESS(f'Safai khatam! {count} purane completed notes delete ho gaye.'))