from rest_framework import serializers
from .models import FeePayment, FeeCategory, StaffSalary, FeeStructure
from django.utils import timezone
from decimal import Decimal
from .models import FeePayment, FeeCategory, FeeStructure, StaffSalary


# 1. Category Serializer (Dropdowns aur Creation ke liye)
class FeeCategorySerializer(serializers.ModelSerializer):
   class Meta:
       model = FeeCategory
       fields = ['id', 'name', 'description', 'is_refundable']

# 2. Detail Serializer (GET Requests - Flutter ki list dikhane ke liye)
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

# 3. Fee Entry Serializer (Fees Jama karne ke liye - POST /collect/)
class FeeEntrySerializer(serializers.ModelSerializer):
   class Meta:
       model = FeePayment
       fields = [
           'student', 'category', 'amount',
           'payment_mode', 'reference_no', 'remarks'
       ]

   def validate_amount(self, value):
       if value <= 0:
           raise serializers.ValidationError("Amount 0 se zyada hona chahiye!")
       return value

   def validate(self, data):
       student = data.get('student')
       request = self.context.get('request')
      
       # 🛡️ School Isolation Check
       school_id = request.headers.get('school_id') or request.headers.get('School-ID')
       if school_id and str(student.organization_id) != str(school_id):
           raise serializers.ValidationError({"student": "Ye student aapke school ka nahi hai!"})

       if not student.is_active:
           raise serializers.ValidationError({"student": "Ye student active nahi hai."})

       return data

   def create(self, validated_data):
       # Agar reference number nahi hai toh auto-generate karo
       if not validated_data.get('reference_no'):
           timestamp = timezone.now().strftime('%Y%m%d%H%M')
           validated_data['reference_no'] = f"PAY-{timestamp}"
       return super().create(validated_data)

# 4. Fee Structure Serializers (Mass Update ke liye)
class FeeHeadSerializer(serializers.Serializer):
   category_id = serializers.IntegerField()
   amount = serializers.DecimalField(max_digits=10, decimal_places=2)

   def validate_amount(self, value):
       if value < 0:
           raise serializers.ValidationError("Fees negative nahi ho sakti!")
       return value

class FeeStructureCreateSerializer(serializers.Serializer):
   standard_id = serializers.IntegerField()
   heads = FeeHeadSerializer(many=True)
  
   # Note: Create logic View mein hai taaki saare sections sync ho sakein.
   # Ye serializer sirf data validate karne ke kaam aayega.


# 1. Admin ke liye - Full Data
class AdminSalarySerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)

    class Meta:
        model = StaffSalary
        fields = '__all__'

# 2. Teacher ke liye - Private Limited Data
class TeacherSalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffSalary
        fields = ['month', 'year', 'amount', 'status', 'paid_date', 'transaction_id', 'payment_mode']