from rest_framework import serializers
from .models import FeePayment, FeeCategory, FeeStructure
from students.models import StudentProfile
from django.utils import timezone

# 1. Category Serializer (Dropdowns ke liye)
class FeeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeCategory
        fields = ['id', 'name']

# 2. Detail Serializer (Data dikhane ke liye - GET Requests)
class FeePaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_uid = serializers.CharField(source='student.student_unique_id', read_only=True)
    class_details = serializers.SerializerMethodField()
    collected_by_name = serializers.CharField(source='collected_by.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    date_formatted = serializers.DateTimeField(source='date', format="%d %b %Y, %I:%M %p", read_only=True)

    class Meta:
        model = FeePayment
        fields = [
            'id', 'student_uid', 'student_name', 'class_details', 
            'amount', 'category_name', 'payment_mode', 
            'reference_no', 'date_formatted', 'collected_by_name', 'remarks'
        ]

    def get_class_details(self, obj):
        if obj.student.current_standard:
            return f"{obj.student.current_standard.name} ({obj.student.current_standard.section})"
        return "N/A"

# 3. Entry Serializer (Data save karne ke liye - POST Requests)
class FeeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeePayment
        fields = [
            'student', 'category', 'amount', 
            'payment_mode', 'reference_no', 'remarks'
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Bhai, amount 0 se zyada hona chahiye!")
        return value

    def validate(self, data):
        student = data.get('student')
        category = data.get('category')
        amount = data.get('amount')

        # 🛡️ ADVANCE CHECK 1: Kya student active hai?
        if not student.is_active:
            raise serializers.ValidationError({"student": "Ye student active nahi hai, fees jama nahi ho sakti."})

        # 🛡️ ADVANCE CHECK 2: Fee Structure Check (Optional but Pro)
        # Dekho ki kya is class ke liye fees set hai?
        structure = FeeStructure.objects.filter(
            standard=student.current_standard, 
            category=category
        ).first()

        if structure and amount > structure.amount:
            # Accountant ko warn karo ya allow na karo agar fees limit se zyada hai
            # Sirf warning ke liye yahan logic dal sakte ho
            pass 

        return data

    def create(self, validated_data):
        # Transaction Reference agar frontend se nahi aaya toh auto-generate karo
        if not validated_data.get('reference_no'):
            timestamp = timezone.now().strftime('%Y%m%d%H%M')
            validated_data['reference_no'] = f"PAY-{timestamp}"
            
        return super().create(validated_data)