import os
import django
import sys
from decimal import Decimal

# 1. Django Environment Setup
# 'school_app' ko replace karo agar tumhare project folder ka naam alag hai
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_app.settings')
django.setup()

# Setup ke baad hi imports karne chahiye
from django.utils import timezone
from django.contrib.auth import get_user_model
from finance.models import FeeCategory, FeeStructure, FeePayment
from students.models import StudentProfile
from students_classroom.models import Standard

User = get_user_model()

def seed_pending_dues():
    print("🚀 Seeding process started...")
    
    # 2. Asli School ID check kar lena Thunder Client se
    SCHOOL_ID = "04c5e7d5-fc60-49b5-9c54-773ffff49304" 
    
    # 3. Superuser/Admin check
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("❌ Error: Pehle ek superuser bana lo (python manage.py createsuperuser)!")
        return

    # 4. Fee Categories
    tuition, _ = FeeCategory.objects.get_or_create(name="Tuition Fee")
    bus, _ = FeeCategory.objects.get_or_create(name="Bus Fee")

    # 5. Fee Structure (Total Udhaar: 20,000)
    standards = Standard.objects.filter(organization_id=SCHOOL_ID)
    if not standards.exists():
        print(f"❌ Error: School ID ({SCHOOL_ID}) ke liye koi Classes nahi mili!")
        return

    for std in standards:
        # Tuition: 15k, Bus: 5k
        FeeStructure.objects.get_or_create(
            standard=std, 
            category=tuition, 
            defaults={'amount': Decimal('15000.00'), 'due_date': timezone.now().date()}
        )
        FeeStructure.objects.get_or_create(
            standard=std, 
            category=bus, 
            defaults={'amount': Decimal('5000.00'), 'due_date': timezone.now().date()}
        )
        print(f"✅ Structure set for: {std.name}")

    # 6. Partial Payments (Sirf 5k Pay karwayenge taaki 15k Pending rahe)
    students = StudentProfile.objects.filter(organization_id=SCHOOL_ID, is_active=True)
    
    count = 0
    for student in students[:15]: 
        FeePayment.objects.create(
            student=student,
            category=tuition,
            amount=Decimal('5000.00'),
            payment_mode='UPI',
            status='SUCCESS',
            collected_by=admin_user,
            remarks="Fake partial payment for testing"
        )
        count += 1
        print(f"💰 Payment added for: {student.user.get_full_name()}")

    print(f"\n✨ Done! {count} students now have pending dues.")
    print("🔗 Thunder Client URL: /api/v1/finance/collection/pending-dues/")

if __name__ == "__main__":
    seed_pending_dues()