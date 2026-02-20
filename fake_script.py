import os
import django
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal

# 1. Django Setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_app.settings') # Apna settings path check kar lena
django.setup()

from students.models import StudentProfile
from finance.models import FeePayment, FeeCategory
from django.contrib.auth import get_user_model

User = get_user_model()

def generate_unique_receipt():
    """Manually generate unique receipt to bypass bulk_create save() skip"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"REC-2026-{suffix}"

def seed_data():
    print("🚀 Advance Finance Data Generation Start...")

    # Categories check/create
    cat_names = ["Tuition Fee", "Admission Fee", "Transport Fee", "Exam Fee", "Library Fee"]
    categories = [FeeCategory.objects.get_or_create(name=name)[0] for name in cat_names]
    
    accountant = User.objects.filter(is_superuser=True).first()
    students = StudentProfile.objects.filter(is_active=True)

    if not students.exists():
        print("❌ Error: No students found!")
        return

    payment_modes = ['CASH', 'UPI', 'BANK_TRANSFER', 'CHEQUE']
    fee_amounts = [1500, 2500, 3500, 5000, 8000]
    
    batch_records = []
    total_count = 0
    start_date = datetime.now() - timedelta(days=150)

    for student in students:
        # Har student ke liye 3 se 5 payments
        for _ in range(random.randint(3, 5)):
            random_days = random.randint(0, 150)
            txn_date = start_date + timedelta(days=random_days)
            
            mode = random.choice(payment_modes)
            ref = f"TXN-{random.randint(100000, 999999)}" if mode != 'CASH' else None

            batch_records.append(
                FeePayment(
                    receipt_no=generate_unique_receipt(), # 🎯 Manual Unique Receipt
                    student=student,
                    category=random.choice(categories),
                    amount=Decimal(random.choice(fee_amounts)),
                    payment_mode=mode,
                    reference_no=ref,
                    status='SUCCESS',
                    collected_by=accountant,
                    remarks="Bulk System Generated",
                    date=txn_date # 🎯 Manual Date
                )
            )

            if len(batch_records) >= 100:
                FeePayment.objects.bulk_create(batch_records)
                total_count += len(batch_records)
                batch_records = []

    if batch_records:
        FeePayment.objects.bulk_create(batch_records)
        total_count += len(batch_records)

    print(f"✅ Success! {total_count} records inserted with unique receipt numbers.")

if __name__ == "__main__":
    seed_data()