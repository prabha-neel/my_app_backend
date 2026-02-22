from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
import pytz
from django.conf import settings
from rest_framework.throttling import UserRateThrottle
from .models import FeePayment, FeeCategory, FeeStructure, StaffSalary
from .serializers import (
  FeePaymentSerializer,
  FeeEntrySerializer,
  FeeCategorySerializer,
  FeeStructureCreateSerializer,
  AdminSalarySerializer
)
from .pagination import FinancePagination

class FeeCollectionViewSet(viewsets.ModelViewSet):
  """
  Advanced Multi-Tenant Fee Management System:
  - Automatic School Isolation (via school_id or School-ID)
  - Secure Collection with Audit Trail
  """
  permission_classes = [IsAuthenticated]
  pagination_class = FinancePagination

  queryset = FeePayment.objects.all().select_related(
      'student__user',
      'student__current_standard',
      'category',
      'collected_by'
  )
  filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
  filterset_fields = ['payment_mode', 'category', 'student', 'status']
  search_fields = ['receipt_no', 'reference_no', 'student__user__first_name']
  ordering_fields = ['date', 'amount']

  def _get_school_id(self, request):
      """Dono hyphen (-) aur underscore (_) headers ko handle karta hai"""
      return request.headers.get('school_id') or request.headers.get('School-ID')

  def get_queryset(self):
      school_id = self._get_school_id(self.request)
      if school_id:
          return self.queryset.filter(student__organization_id=school_id)
      return self.queryset.none()

  def get_serializer_class(self):
      if self.action == 'collect':
          return FeeEntrySerializer
      return FeePaymentSerializer

  @action(detail=False, methods=['get'], url_path='report')
  def get_report(self, request):
      school_id = self._get_school_id(request)
      if not school_id:
          return Response({"error": "school_id header is required!"}, status=status.HTTP_400_BAD_REQUEST)

      from_date = request.query_params.get('from_date')
      to_date = request.query_params.get('to_date')

      qs = self.get_queryset()
      if from_date and to_date:
          qs = qs.filter(date__date__range=[from_date, to_date])

      today = timezone.now().date()
      stats = qs.aggregate(
          total_sum=Sum('amount'),
          online=Sum('amount', filter=Q(payment_mode='Online')),
          offline=Sum('amount', filter=Q(payment_mode='Offline')),
          count=Count('id')
      )
      today_total = qs.filter(date__date=today).aggregate(Sum('amount'))['amount__sum'] or 0

      summary_data = {
          "today_collection": float(today_total),
          "month_collection": float(stats['total_sum'] or 0),
          "pending_dues": 0.0,
          "online_collection": float(stats['online'] or 0),
          "offline_collection": float(stats['offline'] or 0),
          "total_transactions": int(stats['count'] or 0),
      }

      transactions_data = []
      for txn in qs.order_by('-date')[:50]:
          transactions_data.append({
              "student_name": txn.student.user.get_full_name(),
              "class_name": f"{txn.student.current_standard.name if txn.student.current_standard else 'N/A'}",
              "amount": float(txn.amount),
              "payment_mode": txn.payment_mode,
              "transaction_id": txn.receipt_no or str(txn.id),
              "date": txn.date.strftime("%d-%b-%Y"),
          })

      return Response({"summary": summary_data, "transactions": transactions_data})

  @action(detail=False, methods=['post'], url_path='collect')
  @transaction.atomic
  def collect(self, request):
      school_id = self._get_school_id(request)
      if not school_id:
          return Response({"error": "school_id header is required!"}, status=status.HTTP_400_BAD_REQUEST)

      serializer = FeeEntrySerializer(data=request.data, context={'request': request})
      if serializer.is_valid():
          payment = serializer.save(collected_by=request.user)
          return Response({
              "status": "success",
              "message": f"Successfully received ₹{payment.amount}",
              "data": FeePaymentSerializer(payment).data
          }, status=status.HTTP_201_CREATED)
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  @action(detail=False, methods=['get', 'post'])
  def categories(self, request):
      self.pagination_class = None
      if request.method == 'GET':
          serializer = FeeCategorySerializer(FeeCategory.objects.all(), many=True)
          return Response(serializer.data)
     
      if request.method == 'POST':
          serializer = FeeCategorySerializer(data=request.data)
          if serializer.is_valid():
              category = serializer.save()
              return Response(FeeCategorySerializer(category).data, status=201)
          return Response(serializer.errors, status=400)

class FeeStructureViewSet(viewsets.ModelViewSet):
   queryset = FeeStructure.objects.all()
   serializer_class = FeeStructureCreateSerializer
   permission_classes = [IsAuthenticated]

   # 1. GET & CREATE Categories (Heads)
   # Note: Ise humne action banaya hai taaki dropdown aur nayi category manage ho sake
   @action(detail=False, methods=['get', 'post'], url_path='categories')
   def categories(self, request):
       if request.method == 'GET':
           cats = FeeCategory.objects.all()
           serializer = FeeCategorySerializer(cats, many=True)
           return Response(serializer.data)
      
       if request.method == 'POST':
           serializer = FeeCategorySerializer(data=request.data)
           if serializer.is_valid():
               serializer.save()
               return Response(serializer.data, status=201)
           return Response(serializer.errors, status=400)

   # 2. GET Whole Fee Structure (Point 3: With Last Updated At & Unique Class)
   def list(self, request):
       school_id = request.headers.get('school_id') or request.query_params.get('school_id')
       if not school_id:
           return Response({"error": "school_id header required!"}, status=400)

       from students_classroom.models import Standard
       unique_names = Standard.objects.filter(organization_id=school_id).values_list('name', flat=True).distinct()
      
       response_data = []
       indian_timezone = pytz.timezone('Asia/Kolkata') # 🇮🇳 India Timezone

       for name in unique_names:
           any_section = Standard.objects.filter(name=name, organization_id=school_id).first()
           if any_section:
               heads = FeeStructure.objects.filter(standard=any_section)
               if heads.exists():
                   latest = heads.order_by('-updated_at').first()
                  
                   # 🕒 Convert UTC to IST
                   ist_time = latest.updated_at.astimezone(indian_timezone)
                  
                   response_data.append({
                       "id": str(any_section.id),
                       "class_name": name.capitalize(),
                       "fee_type": "Monthly",
                       "last_updated_at": ist_time.strftime("%d-%b-%Y %I:%M %p"), # 👈 Ab 11:53 AM aayega
                       "heads": [{"category_id": h.category.id, "title": h.category.name, "amount": float(h.amount)} for h in heads]
                   })
       return Response(response_data)
   # 3. CREATE for Whole Class (Point 2: Admin sets for all sections)
   def create(self, request):
       serializer = FeeStructureCreateSerializer(data=request.data)
       if serializer.is_valid():
           v_data = serializer.validated_data
           standard_id = v_data['standard_id']
           heads_data = v_data['heads']

           from students_classroom.models import Standard
           target_std = Standard.objects.get(id=standard_id)
           # Saare sections pakdo: A, B, C...
           all_sections = Standard.objects.filter(name=target_std.name, organization_id=target_std.organization_id)

           with transaction.atomic():
               for std in all_sections:
                   for head in heads_data:
                       FeeStructure.objects.update_or_create(
                           standard=std,
                           category_id=head['category_id'],
                           defaults={'amount': head['amount'], 'due_date': timezone.now().date()}
                       )
           return Response({"status": "success", "message": f"Structure set for all sections of {target_std.name}"}, status=201)
       return Response(serializer.errors, status=400)

   # 4. DELETE (Point 4: Independent Delete, no dependencies)
   def destroy(self, request, pk=None):
       school_id = request.headers.get('school_id')
       from students_classroom.models import Standard
       try:
           target_std = Standard.objects.get(id=pk, organization_id=school_id)
           all_sections = Standard.objects.filter(name=target_std.name, organization_id=school_id)
          
           # Seeda delete, koi check nahi
           FeeStructure.objects.filter(standard__in=all_sections).delete()
           return Response({"message": "Deleted successfully"}, status=200)
       except Standard.DoesNotExist:
           return Response({"error": "Not found"}, status=404)


class SalaryManagementViewSet(viewsets.ModelViewSet):
    # 'select_related' lagaya hai taaki database query fast ho (Industry Level)
    queryset = StaffSalary.objects.all().select_related('teacher__user', 'processed_by')
    serializer_class = AdminSalarySerializer
    permission_classes = [IsAuthenticated] 
    throttle_classes = [UserRateThrottle] # Rate limiting protection

    def get_queryset(self):
        # Strict School Isolation
        school_id = self.request.headers.get('school_id') or self.request.headers.get('School-ID')
        if not school_id:
            return self.queryset.none()
        return self.queryset.filter(teacher__organization_id=school_id)

    @transaction.atomic
    def perform_create(self, serializer):
        # Salary approve karne wale admin ka record auto-save
        serializer.save(processed_by=self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save(processed_by=self.request.user)