from rest_framework import serializers
from .models import StudentProfile, StudentSession, StudentResult, StudentFee, ParentConnection
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from attendance.models import Attendance


User = get_user_model()

# ────────────────────────────────────────────────
# 1. Minimal Serializer (Search & Explore ke liye)
# ────────────────────────────────────────────────
class StudentMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    section = serializers.SerializerMethodField()
    # 🚩 Yahan humne key ka naam badal kar student_id kar diya
    student_id = serializers.SerializerMethodField() 
    school_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id", 
            "full_name", 
            "class_name", 
            "section", 
            "student_id", # Nayi key
            "school_name", 
            "organization"
        ]

    def get_student_id(self, obj):
        # 💡 Wahi "Count" wala logic jo pagination aur search mein stable rehta hai
        if not obj.current_standard:
            return 0
        
        count = StudentProfile.objects.filter(
            current_standard=obj.current_standard,
            created_at__lt=obj.created_at
        ).count()
        
        return count + 1

    def get_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "Unknown"

    def get_class_name(self, obj):
        return obj.current_standard.name if obj.current_standard else "N/A"

    def get_section(self, obj):
        return getattr(obj.current_standard, 'section', 'N/A')


# ────────────────────────────────────────────────
# 2. Detailed Profile Serializer
# ────────────────────────────────────────────────
class StudentProfileSerializer(serializers.ModelSerializer):
    """
    Detailed view for Admins, Teachers, and the Student themselves.
    """
    full_name = serializers.SerializerMethodField()
    mobile = serializers.CharField(source='user.mobile', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id", "student_unique_id", "full_name", "mobile", "email",
            "organization", "current_standard", "is_active", "created_at"
        ]
        read_only_fields = ["student_unique_id", "created_at"]

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()


# ────────────────────────────────────────────────
# 3. Session Serializer (Point #6, #7, #8)
# ────────────────────────────────────────────────
class StudentSessionSerializer(serializers.ModelSerializer):
    """
    Teacher/Admin jo sessions create karte hain.
    """
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = StudentSession
        fields = [
            "id", "session_code", "title", "student_limit", 
            "expires_at", "status", "created_by_name"
        ]
        read_only_fields = ["session_code", "status"]


# ────────────────────────────────────────────────
# 4. Academic & Finance Serializers (Point #4)
# ────────────────────────────────────────────────
class StudentResultSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    exam_name = serializers.CharField(source='exam.title', read_only=True)

    class Meta:
        model = StudentResult
        fields = ["id", "exam_name", "subject_name", "marks_obtained", "total_marks", "grade", "remarks"]

class StudentFeeSerializer(serializers.ModelSerializer):
    fee_type_display = serializers.CharField(source='fee_type.name', read_only=True)

    class Meta:
        model = StudentFee
        fields = ["id", "fee_type_display", "amount", "due_date", "status", "paid_at"]

    

class ParentRequestSerializer(serializers.ModelSerializer):
    student_username = serializers.CharField(write_only=True)
    # Bache ki thodi info dikhane ke liye (Optional but good for Flutter)
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)

    class Meta:
        model = ParentConnection
        fields = ['id', 'student_username', 'student_name', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']

    def validate_student_username(self, value):
        try:
            student_user = User.objects.get(username=value)
            
            # 1. Security Check: Khud ko request nahi bhej sakte
            if student_user == self.context['request'].user:
                raise serializers.ValidationError("Bhai, tum khud ke bache nahi ban sakte!")

            # 2. Check: Kya uski Student Profile hai?
            if not hasattr(student_user, 'student_profile'):
                raise serializers.ValidationError("Ye user student nahi hai!")
                
            return student_user.student_profile
        except User.DoesNotExist:
            raise serializers.ValidationError("Bhai, is username ka koi bacha nahi mila!")

    def create(self, validated_data):
        user = self.context['request'].user
        student_profile = validated_data['student_username']
        
        # Connection logic: Agar PENDING ya ACCEPTED hai toh error do
        existing = ParentConnection.objects.filter(user=user, student=student_profile).first()
        
        if existing:
            if existing.status == 'PENDING':
                raise serializers.ValidationError("Aapki request pehle se pending hai.")
            if existing.status == 'ACCEPTED':
                raise serializers.ValidationError("Aap pehle se hi is bache ke parent ho.")
            
            # Agar purani request REJECTED thi, toh use wapas PENDING kar do
            existing.status = 'PENDING'
            existing.save()
            return existing
        
        return ParentConnection.objects.create(user=user, student=student_profile)


class StudentSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    personal_details = serializers.SerializerMethodField()
    attendance_stats = serializers.SerializerMethodField()
    fee_stats = serializers.SerializerMethodField()
    academic_stats = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'student_unique_id', 'full_name', 
            'personal_details', 'attendance_stats', 
            'fee_stats', 'academic_stats'
        ]

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_personal_details(self, obj):
        # 💡 Data 'NormalUser' model se aa raha hai
        user = obj.user
        return {
            "email": user.email,
            "mobile": user.mobile,
            "gender": user.get_gender_display() if user.gender else "N/A",
            "blood_group": user.bloodgroup or "N/A",
            "dob": user.dob,
            "address": user.address or "N/A",
            "current_standard": obj.current_standard.name if obj.current_standard else "Not Assigned",
            "roll_no": obj.student_unique_id,
            "bio": obj.bio or ""
        }

    def get_attendance_stats(self, obj):
        # 💡 Model 'Attendance' se link hai (related_name='attendance_records')
        records = obj.attendance_records.all()
        total = len(records)
        present = len([r for r in records if r.status == 'PRESENT'])
        
        return {
            "total": total,
            "present": present,
            "absent": total - present,
            "percentage": round((present / total * 100), 2) if total > 0 else 0
        }

    def get_fee_stats(self, obj):
        # 💡 Asli transactions 'FeePayment' model mein hain (related_name='fee_payments')
        payments = obj.fee_payments.all()
        
        total_paid = sum(p.amount for p in payments if p.status == 'SUCCESS')
        
        # History map kar rahe hain FeePayment se
        history = [{
            "receipt_no": p.receipt_no,
            "amount": float(p.amount),
            "date": p.date.strftime('%Y-%m-%d %H:%M'),
            "mode": p.get_payment_mode_display(),
            "status": p.status,
            "category": p.category.name
        } for p in payments]

        return {
            "summary": {
                "total_paid": float(total_paid),
                "transaction_count": len(payments)
            },
            "history": history
        }

    def get_academic_stats(self, obj):
        # 💡 'StudentResult' model se link hai
        results = obj.results.all()
        if not results:
            return {"average_score": 0, "recent_results": []}
            
        total_marks = sum(r.marks_obtained for r in results)
        total_max = sum(r.total_marks for r in results)
        
        return {
            "average_percentage": round((total_marks / total_max * 100), 2) if total_max > 0 else 0,
            "recent_results": [{
                "exam": r.exam_name,
                "marks": f"{r.marks_obtained}/{r.total_marks}",
                "date": r.exam_date,
                "grade": r.grade
            } for r in results[:5]]
        }