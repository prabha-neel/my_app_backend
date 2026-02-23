from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from organizations.models import Organization
from students_classroom.models import Standard
from teachers.models import Teacher
from .models import Subject, WeeklyTimetable
from .serializers import MasterBulkSetupSerializer
from .permissions import IsSchoolAdmin

class MasterClassSetupView(APIView):
    # Isse ab sirf wahi user ghus payega jo logged-in hai aur SCHOOL_ADMIN hai
    permission_classes = [IsAuthenticated, IsSchoolAdmin] 

    @transaction.atomic
    def post(self, request):
        # 1. Serializer ab 'School-ID' bhejoge toh accept karega (source mapping ki wajah se)
        serializer = MasterBulkSetupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # 2. Data extraction (organization_id internally 'School-ID' se map ho gaya hai)
        data = serializer.validated_data
        org_id = data.get('organization_id')
        sections_data = data.get('sections_data', [])

        # 3. Security Check: Kya logged-in admin isi School ka owner hai?
        try:
            org_obj = Organization.objects.get(id=org_id, admin=request.user)
        except Organization.DoesNotExist:
            return Response({"error": "Bhai, ye school aapka nahi hai!"}, status=403)

        try:
            for section in sections_data:
                # 4. Section ko dhoondo (Confirm karo ki ye isi Org ka hai)
                try:
                    standard_obj = Standard.objects.get(id=section['standard_id'], organization=org_obj)
                except Standard.DoesNotExist:
                    return Response({"error": f"Section ID {section['standard_id']} is school mein nahi hai."}, status=404)

                # 5. CLASS TEACHER UPDATE (Purana overwrite hoga)
                if section.get('class_teacher_id'):
                    standard_obj.class_teacher_id = section['class_teacher_id']
                    standard_obj.save(update_fields=['class_teacher'])

                # 6. TIMETABLE LOGIC
                days = section['days']
                periods = section['periods']

                for day_code in days:
                    # Purana schedule saaf karo taaki naya fresh save ho sake
                    WeeklyTimetable.objects.filter(standard=standard_obj, day=day_code).delete()

                    for p in periods:
                        # Conflict Check: Kya ye teacher isi waqt kisi doosre section mein hai?
                        conflict = WeeklyTimetable.objects.filter(
                            organization=org_obj,
                            day=day_code,
                            period_number=p['period_number'],
                            teacher_id=p['teacher_id']
                        ).exclude(standard=standard_obj).first()

                        if conflict:
                            teacher_name = Teacher.objects.get(id=p['teacher_id']).user.get_full_name()
                            return Response({
                                "error": f"Conflict! {teacher_name} {day_code} P{p['period_number']} mein Class {conflict.standard.name} mein busy hain."
                            }, status=400)

                        # Subject creation/retrieval (Unique per organization)
                        sub_obj, _ = Subject.objects.get_or_create(
                            organization=org_obj,
                            name=p['subject_name'].strip().capitalize()
                        )

                        # Save new entry
                        WeeklyTimetable.objects.create(
                            organization=org_obj,
                            standard=standard_obj,
                            day=day_code,
                            period_number=p['period_number'],
                            subject=sub_obj,
                            teacher_id=p['teacher_id']
                        )

            return Response({"message": f"Mubarak ho! {org_obj.name} ka setup update ho gaya."}, status=201)

        except Exception as e:
            # Agar koi bhi error aaye toh transaction rollback ho jayega
            return Response({"error": f"Kuch locha hua: {str(e)}"}, status=400)
        
    def get(self, request):
        # 🔥 FIX: Dono parameters check karo, pehle 'School-ID' phir 'organization_id'
        org_id = request.query_params.get('School-ID')
        standard_id = request.query_params.get('standard_id')

        # Error message bhi update kar dete hain taaki confusion na ho
        if not org_id:
            return Response({"error": "School-ID parameter zaroori hai!"}, status=400)

        # Base query (Internal filter hamesha organization_id hi rahega)
        qs = WeeklyTimetable.objects.filter(organization_id=org_id).select_related(
            'standard', 'standard__class_teacher__user', 'subject', 'teacher__user'
        )

        # Agar specific class ka dekhna hai
        if standard_id:
            qs = qs.filter(standard_id=standard_id)

        # Formatting the response
        data = []
        for entry in qs:
            data.append({
                "day": entry.day,
                "period": entry.period_number,
                "subject": entry.subject.name,
                "subject_teacher": entry.teacher.user.get_full_name(), # Padhane wala
                "section": entry.standard.name,
                # 🔥 Ab yahan se pata chalega "Class Teacher" kaun hai:
                "class_teacher": entry.standard.class_teacher.user.get_full_name() if entry.standard.class_teacher else "Not Assigned",
                "is_class_teacher_period": (entry.standard.class_teacher == entry.teacher) # Kya ye period class teacher khud le raha hai?
            })

        return Response(data, status=200)