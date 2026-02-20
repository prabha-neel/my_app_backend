import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import datetime  # 👈 Ye line missing hai

class FeeCategory(models.Model):
    """Fees ke types: Tuition, Exam, Transport, Library etc."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_refundable = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Fee Categories"

    def __str__(self):
        return self.name

class FeeStructure(models.Model):
    """Class wise predefined fees taaki accountant ko pata ho kitna lena hai"""
    standard = models.ForeignKey('students_classroom.Standard', on_delete=models.CASCADE, related_name='fee_structures')
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    due_date = models.DateField(help_text="Is mahine ki wo date jab tak fees bharni hai")

    class Meta:
        unique_together = ('standard', 'category')

    def __str__(self):
        return f"{self.standard.name} - {self.category.name}: {self.amount}"

class FeePayment(models.Model):
    """Asli transaction records"""
    PAYMENT_MODES = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI/Online'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
    ]

    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('PENDING', 'Pending/Verification'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    # Unique Transaction ID for Receipt
    receipt_no = models.CharField(max_length=50, unique=True, editable=False)
    
    student = models.ForeignKey('students.StudentProfile', on_delete=models.PROTECT, related_name='fee_payments')
    category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES, default='CASH')
    reference_no = models.CharField(max_length=100, blank=True, null=True, help_text="Txn ID or Cheque No.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUCCESS')
    
    # Audit Fields
    collected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='collected_fees')
    date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            # Automatic Receipt Number Generation: REC-2026-XXXX
            import random
            year = datetime.now().year
            unique_id = ''.join(random.choices('0123456789ABCDEF', k=6))
            self.receipt_no = f"REC-{year}-{unique_id}"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.receipt_no} - {self.student.user.get_full_name()}"