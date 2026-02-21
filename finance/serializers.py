# from rest_framework import serializers
# from .models import FeePayment, FeeCategory, FeeStructure
# from students.models import StudentProfile
# from django.utils import timezone

# # 1. Category Serializer (Dropdowns ke liye)
# class FeeCategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FeeCategory
#         fields = ['id', 'name']

# # 2. Detail Serializer (Data dikhane ke liye - GET Requests)
# class FeePaymentSerializer(serializers.ModelSerializer):
#     student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
#     student_uid = serializers.CharField(source='student.student_unique_id', read_only=True)
#     class_details = serializers.SerializerMethodField()
#     collected_by_name = serializers.CharField(source='collected_by.get_full_name', read_only=True)
#     category_name = serializers.CharField(source='category.name', read_only=True)
#     date_formatted = serializers.DateTimeField(source='date', format="%d %b %Y, %I:%M %p", read_only=True)

#     class Meta:
#         model = FeePayment
#         fields = [
#             'id', 'student_uid', 'student_name', 'class_details',
#             'amount', 'category_name', 'payment_mode',
#             'reference_no', 'date_formatted', 'collected_by_name', 'remarks'
#         ]

#     def get_class_details(self, obj):
#         if obj.student.current_standard:
#             return f"{obj.student.current_standard.name} ({obj.student.current_standard.section})"
#         return "N/A"

# # 3. Entry Serializer (Data save karne ke liye - POST Requests)
# class FeeEntrySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FeePayment
#         fields = [
#             'student', 'category', 'amount',
#             'payment_mode', 'reference_no', 'remarks'
#         ]

#     def validate_amount(self, value):
#         if value <= 0:
#             raise serializers.ValidationError("Bhai, amount 0 se zyada hona chahiye!")
#         return value

#     def validate(self, data):
#         student = data.get('student')
#         category = data.get('category')
#         amount = data.get('amount')

#         # 🛡️ ADVANCE CHECK 1: Kya student active hai?
#         if not student.is_active:
#             raise serializers.ValidationError({"student": "Ye student active nahi hai, fees jama nahi ho sakti."})

#         # 🛡️ ADVANCE CHECK 2: Fee Structure Check (Optional but Pro)
#         # Dekho ki kya is class ke liye fees set hai?
#         structure = FeeStructure.objects.filter(
#             standard=student.current_standard,
#             category=category
#         ).first()

#         if structure and amount > structure.amount:
#             # Accountant ko warn karo ya allow na karo agar fees limit se zyada hai
#             # Sirf warning ke liye yahan logic dal sakte ho
#             pass

#         return data

#     def create(self, validated_data):
#         # Transaction Reference agar frontend se nahi aaya toh auto-generate karo
#         if not validated_data.get('reference_no'):
#             timestamp = timezone.now().strftime('%Y%m%d%H%M')
#             validated_data['reference_no'] = f"PAY-{timestamp}"
          
#         return super().create(validated_data)
  
# # finance/serializers.py mein ye add karo
# class FeeHeadSerializer(serializers.Serializer):
#     category_id = serializers.IntegerField()
#     amount = serializers.DecimalField(max_digits=10, decimal_places=2)

# class FeeStructureCreateSerializer(serializers.Serializer):
#     standard_id = serializers.IntegerField()
#     heads = FeeHeadSerializer(many=True)

#     def create(self, validated_data):
#         standard_id = validated_data['standard_id']
#         heads_data = validated_data['heads']
#         structures = []

#         for head in heads_data:
#             # 🛡️ Ye line magic hai: Agar entry hai toh update, warna create
#             struct, created = FeeStructure.objects.update_or_create(
#                 standard_id=standard_id,
#                 category_id=head['category_id'],
#                 defaults={
#                     'amount': head['amount'],
#                     'due_date': "2026-04-10" # Default date for now
#                 }
#             )
#             structures.append(struct)
#         return structures



from rest_framework import serializers
from .models import FeePayment, FeeCategory, FeeStructure
from django.utils import timezone
from decimal import Decimal

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

