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
from django.db.models import Count
from .serializers import StaffMemberSerializer, StaffAttendanceSerializer 


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
    
    @action(detail=True, methods=['get'], url_path='monthly-report')
    def monthly_report(self, request, pk=None):
        """
        URL: /api/v1/staff/staff-attendance/<user_id>/monthly-report/?month=2&year=2026
        """
        org_id = self.get_org_id(request)
        if not org_id:
            return Response({"error": "School_ID header missing"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Month aur Year handle karo (Default: Current Month)
        now = timezone.now()
        month = int(request.query_params.get('month', now.month))
        year = int(request.query_params.get('year', now.year))

        # 2. Specific Teacher/Staff ka data nikalo
        # pk yahan user_id hai kyunki detail=True hai
        attendance_records = StaffAttendance.objects.filter(
            organization_id=org_id,
            user_id=pk,
            date__month=month,
            date__year=year
        ).order_by('date')

        # 3. Summary calculate karo (Kitne din Present, Absent, etc.)
        summary = attendance_records.values('status').annotate(count=Count('status'))

        # 4. Data format karo
        serializer = StaffAttendanceSerializer(attendance_records, many=True)
        
        return Response({
            "user_id": pk,
            "month": month,
            "year": year,
            "summary": {item['status']: item['count'] for item in summary},
            "records": serializer.data
        })