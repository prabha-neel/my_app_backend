from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.throttling import ScopedRateThrottle
from django.utils import timezone

from teachers.models import Teacher
from organizations.models import SchoolAdmin
from normal_user.models import NormalUser
from .models import StaffAttendance
from .serializers import StaffMemberSerializer
from .permissions import IsSchoolAdmin

class StaffAttendanceViewSet(viewsets.ViewSet):
    # 🔐 Security Layers
    permission_classes = [IsSchoolAdmin]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'attendance_ops'

    def get_org_id(self, request):
        return request.headers.get('School_ID')

    @action(detail=False, methods=['get'], url_path='get-staff-list')
    def get_staff_list(self, request):
        org_id = self.get_org_id(request)
        if not org_id:
            return Response({"error": "School_ID header missing"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. School se linked Staff nikalna
        teacher_user_ids = Teacher.objects.filter(organization_id=org_id, is_active_teacher=True).values_list('user_id', flat=True)
        admin_user_ids = SchoolAdmin.objects.filter(organization_id=org_id, is_active=True).values_list('user_id', flat=True)
        staff_ids = set(list(teacher_user_ids) + list(admin_user_ids))
        
        staff_users = NormalUser.objects.filter(id__in=staff_ids)
        
        # 2. Attendance Status
        date_query = request.query_params.get('date', timezone.now().date())
        attendance_records = StaffAttendance.objects.filter(organization_id=org_id, date=date_query)
        att_dict = {str(a.user.id): {"status": a.status, "in": a.punch_in, "out": a.punch_out} for a in attendance_records}

        serializer = StaffMemberSerializer(staff_users, many=True)
        
        final_data = []
        for user_data in serializer.data:
            att_info = att_dict.get(str(user_data['id']), None)
            user_data['today_attendance'] = att_info if att_info else {"status": "NOT_MARKED"}
            final_data.append(user_data)

        return Response(final_data)

    @action(detail=False, methods=['post'], url_path='bulk-mark')
    def bulk_mark(self, request):
        org_id = self.get_org_id(request)
        attendance_list = request.data.get('attendance_data', [])
        date_val = request.data.get('date', timezone.now().date())

        if not org_id:
            return Response({"error": "School_ID header missing"}, status=status.HTTP_400_BAD_REQUEST)

        for item in attendance_list:
            StaffAttendance.objects.update_or_create(
                organization_id=org_id,
                user_id=item.get('user_id'),
                date=date_val,
                defaults={
                    'status': item.get('status', 'PRESENT'),
                    'marked_by': request.user,
                    'punch_in': item.get('punch_in'),
                    'punch_out': item.get('punch_out'),
                    'remark': item.get('remark')
                }
            )
        return Response({"message": "Attendance updated successfully!"}, status=status.HTTP_200_OK)