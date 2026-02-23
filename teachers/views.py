#teachers\views.py

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import Teacher
from .serializers import TeacherPublicSerializer, TeacherProfileSerializer
from .permissions import IsTeacherOwnerOrSchoolAdmin
from finance.models import StaffSalary
from finance.serializers import TeacherSalarySerializer
from rest_framework.permissions import IsAuthenticated 
from django.db import transaction
from academics.models import WeeklyTimetable
from students_classroom.models import Standard


class TeacherViewSet(viewsets.ModelViewSet):
    """
    Objective #4, #5: Handle Independent & School Teachers
    """
    queryset = Teacher.objects.filter(is_active_teacher=True)
    permission_classes = [IsTeacherOwnerOrSchoolAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Marketplace Filtering
    filterset_fields = ['is_verified', 'preferred_mode', 'organization']
    search_fields = ['user__first_name', 'user__last_name', 'bio', 'subject_expertise']
    ordering_fields = ['hourly_rate', 'experience_years']

    def get_serializer_class(self):
        if self.action in ['list', 'marketplace']:
            return TeacherPublicSerializer
        return TeacherProfileSerializer

    # ==================================================================================================
# =================================shivam changes ==================================================
# ==================================================================================================
    @action(detail=False, methods=['get'], url_path='dropdown-list')
    def dropdown_list(self, request):
       """
       🚀 Clean Teacher List:
       Sirf ID, Name aur Primary Subject bhejega.
       """
       school_id = request.headers.get('School-ID') or request.headers.get('school_id')
      
       # Base filters (Security first)
       queryset = self.queryset
       if school_id:
           queryset = queryset.filter(organization_id=school_id)

       # Response format karna
       formatted_data = []
       for teacher in queryset.select_related('user'):
           # Maan lo subject_expertise ek JSON field hai ya Dict hai
           subject_info = teacher.subject_expertise
           primary_subject = "General"
          
           # Agar subject_expertise string hai toh seedha use karo,
           # agar dict/JSON hai toh 'primary' key uthao
           if isinstance(subject_info, dict):
               primary_subject = subject_info.get('primary', 'General')
           elif isinstance(subject_info, str):
               primary_subject = subject_info

           formatted_data.append({
               "id": str(teacher.id),
               "full_name": teacher.user.get_full_name(),
               "subject": primary_subject
           })
      
       return Response(formatted_data, status=200)

# ==================================================================================================

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        """Teacher apni profile /api/teachers/me/ par manage karega"""
        teacher = get_object_or_404(Teacher, user=request.user)
        if request.method == 'GET':
            serializer = TeacherProfileSerializer(teacher)
            return Response(serializer.data)
        
        serializer = TeacherProfileSerializer(teacher, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='join-school')
    def join_school_request(self, request):
        """
        Objective #3: Teacher join request logic using session_code.
        """
        # Circular import se bachne ke liye import yahan andar kiya hai
        from students_classroom.models import ClassroomSession, JoinRequest
        
        # 1. Frontend se Code uthao (e.g. "CLS-X7Y2Z")
        session_code = request.data.get('session_code') 
        
        if not session_code:
            return Response({"error": "Session code is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Database mein session check karo
        session = get_object_or_404(
            ClassroomSession.objects.active(), # Sirf wahi jo delete nahi hue
            session_code=session_code
        )

        # 3. Check karo session joinable hai (Time aur Capacity check)
        if not session.is_joinable:
            return Response(
                {"error": f"This session is currently {session.status}. It might be expired or full."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Join Request create karo (Ya existing wali uthao)
        join_request, created = JoinRequest.objects.get_or_create(
            session=session,
            user=request.user,
            defaults={'status': 'PENDING'}
        )

        if not created:
            return Response(
                {"message": f"You have already sent a request. Current status: {join_request.status}"}, 
                status=status.HTTP_200_OK
            )

        return Response(
            {"message": "Join request sent successfully! Wait for school admin to accept."}, 
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='remove-from-school')
    @transaction.atomic
    def remove_from_school(self, request, pk=None):
        """
        Bhai ye function strictly teacher ko organization se unlink karega,
        unka data safe rakhega aur purane role par wapas bhej dega.
        """
        try:
            # 1. Teacher ko direct fetch karo (Avoid RelatedManager error)
            # pk wahi UUID hai jo URL mein aa rahi hai
            try:
                teacher = Teacher.objects.get(pk=pk)
            except Teacher.DoesNotExist:
                return Response({"error": "Teacher record nahi mila!"}, status=404)

            # 2. Check karo ki teacher kisi school se juda bhi hai ya nahi
            org_obj = teacher.organization
            if not org_obj:
                return Response({"error": "Ye teacher pehle se hi kisi school se juda nahi hai."}, status=400)

            # 3. Security Check: Kya ye request karne wala Admin isi school ka owner hai?
            if org_obj.admin != request.user:
                return Response({"error": "Bhai, aapke paas is teacher ko hatane ka haq nahi hai!"}, status=403)

            user = teacher.user

            # 4. TIMETABLE CLEANUP
            # School ke timetable se is teacher ki entries saaf karo
            WeeklyTimetable.objects.filter(organization=org_obj, teacher=teacher).delete()
            
            # 5. CLASS TEACHER REMOVAL
            # Agar kisi class ka class teacher tha, toh wo slot khali karo
            Standard.objects.filter(organization=org_obj, class_teacher=teacher).update(class_teacher=None)

            # 6. ROLE RESTORATION
            # Qualifications ke basis par Independent Teacher ya Normal User banao
            if not teacher.qualifications or not teacher.qualifications.strip():
                user.role = 'NORMAL_USER'
            else:
                user.role = 'TEACHER' # Restore as Independent Teacher
            user.save()

            # 7. THE UNLINK (Main Step)
            # Record delete nahi hoga (Attendance/Fees safe), sirf school se nata tutega
            teacher.organization = None
            teacher.is_active_teacher = True # Marketplace ke liye active rahega
            teacher.save()

            return Response({
                "status": "success",
                "message": f"{user.get_full_name()} ko {org_obj.name} se safaltapoorvak hata diya gaya hai. Purana data (Attendance/Fees) safe hai."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Ab ye error detail mein bata dega agar koi naya locha hua toh
            return Response({"error": f"Locha ho gaya: {str(e)}"}, status=400)
    

class MySalaryView(viewsets.ReadOnlyModelViewSet):
    """Teacher logged in hai toh sirf apna hi data dekhega"""
    serializer_class = TeacherSalarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Database level filter on request.user (Security Layer)
        return StaffSalary.objects.filter(teacher__user=self.request.user).order_by('-year', '-month')