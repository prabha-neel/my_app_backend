# from django.db import transaction
# from django.db.models import Sum, Count, Q
# from django.utils import timezone
# from rest_framework import viewsets, status, filters
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django_filters.rest_framework import DjangoFilterBackend

# from .models import FeePayment, FeeCategory, FeeStructure
# from .serializers import (
#     FeePaymentSerializer,
#     FeeEntrySerializer,
#     FeeCategorySerializer
# )
# from .pagination import FinancePagination

# class FeeCollectionViewSet(viewsets.ModelViewSet):
#     """
#     Khatarnak Multi-Tenant Fee Management System:
#     - Automatic School Isolation via Headers (school_id or School-ID)
#     - Paginated Transactions & History
#     - Deep Dashboard Analytics
#     - Smart Pending Dues Calculation
#     """
#     permission_classes = [IsAuthenticated]
#     pagination_class = FinancePagination

#     queryset = FeePayment.objects.all().select_related(
#         'student__user',
#         'student__current_standard',
#         'category',
#         'collected_by'
#     )
  
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     filterset_fields = ['payment_mode', 'category', 'student', 'status']
#     search_fields = [
#         'receipt_no',
#         'reference_no',
#         'student__user__first_name',
#         'student__student_unique_id'
#     ]
#     ordering_fields = ['date', 'amount']

#     # ────────────────────────────────────────────────
#     # 🛠️ HELPER: Get School ID from any Header
#     # ────────────────────────────────────────────────
#     def _get_school_id(self, request):
#         """Standardizes school ID retrieval from headers"""
#         return request.headers.get('school_id') or request.headers.get('School-ID')

#     def get_queryset(self):
#         """Filters all data based on the provided school ID"""
#         school_id = self._get_school_id(self.request)
#         base_qs = self.queryset

#         if school_id:
#             return base_qs.filter(student__organization_id=school_id)
      
#         return base_qs.none()

#     def get_serializer_class(self):
#         if self.action == 'collect':
#             return FeeEntrySerializer
#         return FeePaymentSerializer

#     # ────────────────────────────────────────────────
#     # 📊 DASHBOARD ANALYTICS
#     # ────────────────────────────────────────────────
#     @action(detail=False, methods=['get'], url_path='dashboard-summary')
#     def dashboard_summary(self, request):
#         qs = self.get_queryset()
#         today = timezone.now().date()
#         month_start = today.replace(day=1)

#         summary = {
#             "stats": {
#                 "today_total": qs.filter(date__date=today).aggregate(Sum('amount'))['amount__sum'] or 0,
#                 "monthly_total": qs.filter(date__date__gte=month_start).aggregate(Sum('amount'))['amount__sum'] or 0,
#                 "total_count": qs.count(),
#             },
#             "payment_methods": qs.values('payment_mode').annotate(
#                 total_amount=Sum('amount'),
#                 count=Count('id')
#             ),
#             "recent_activity": FeePaymentSerializer(
#                 qs.order_by('-date')[:5],
#                 many=True,
#                 context={'request': request}
#             ).data
#         }
#         return Response(summary)

#     # ────────────────────────────────────────────────
#     # 💰 SECURE COLLECTION
#     # ────────────────────────────────────────────────
#     @action(detail=False, methods=['post'], url_path='collect')
#     @transaction.atomic
#     def collect(self, request):
#         school_id = self._get_school_id(request)
#         if not school_id:
#             return Response({"error": "school_id header is required!"}, status=status.HTTP_400_BAD_REQUEST)

#         serializer = FeeEntrySerializer(data=request.data, context={'request': request})
      
#         if serializer.is_valid():
#             payment = serializer.save(collected_by=request.user)
#             return Response({
#                 "status": "success",
#                 "message": f"Successfully received ₹{payment.amount}",
#                 "receipt_no": payment.receipt_no,
#                 "data": FeePaymentSerializer(payment, context={'request': request}).data
#             }, status=status.HTTP_201_CREATED)
          
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     # ────────────────────────────────────────────────
#     # 📜 STUDENT TRANSACTION HISTORY
#     # ────────────────────────────────────────────────
#     @action(detail=True, methods=['get'], url_path='history')
#     def student_history(self, request, pk=None):
#         history = self.get_queryset().filter(student_id=pk).order_by('-date')
      
#         page = self.paginate_queryset(history)
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return self.get_paginated_response(serializer.data)

#         serializer = self.get_serializer(history, many=True)
#         return Response(serializer.data)

#     # ────────────────────────────────────────────────
#     # 📂 CATEGORIES (Dropdowns)
#     # ────────────────────────────────────────────────
#     @action(detail=False, methods=['get'])
#     def categories(self, request):
#         self.pagination_class = None
#         cats = FeeCategory.objects.all()
#         serializer = FeeCategorySerializer(cats, many=True)
#         return Response(serializer.data)

#     # ────────────────────────────────────────────────
#     # 🕵️ PENDING DUES (Error Fixed Version)
#     # ────────────────────────────────────────────────
#     @action(detail=False, methods=['get'], url_path='pending-dues')
#     def pending_dues(self, request):
#         school_id = self._get_school_id(request)
#         if not school_id:
#             return Response({"error": "school_id header is required!"}, status=status.HTTP_400_BAD_REQUEST)

#         from students.models import StudentProfile
#         # 🎯 FIX: 'current_section' hata diya kyunki ye model mein nahi hai
#         students = StudentProfile.objects.filter(
#             organization_id=school_id,
#             is_active=True
#         ).select_related('user', 'current_standard')

#         pending_list = []
      
#         for student in students:
#             # 1. Fee Structure check
#             structure = FeeStructure.objects.filter(
#                 standard=student.current_standard
#             ).first()

#             if not structure:
#                 continue

#             # 2. Total paid calculation
#             total_paid = FeePayment.objects.filter(
#                 student=student,
#                 status='SUCCESS'
#             ).aggregate(Sum('amount'))['amount__sum'] or 0

#             # 3. Defaulter identification
#             if total_paid < structure.amount:
#                 last_payment = FeePayment.objects.filter(student=student).order_by('-date').first()
              
#                 # 🎯 Safe extraction for section and roll number
#                 pending_list.append({
#                     "student_id": str(student.id),
#                     "name": student.user.get_full_name(),
#                     "roll_no": getattr(student, 'roll_number', 'N/A'),
#                     "class_name": student.current_standard.name if student.current_standard else "N/A",
#                     # Agar section field ka naam alag hai toh yahan badal lena
#                     "section_name": getattr(student, 'section', 'N/A'),
#                     "total_required": float(structure.amount),
#                     "total_paid": float(total_paid),
#                     "due_amount": float(structure.amount - total_paid),
#                     "last_paid_date": last_payment.date.strftime("%d-%b-%Y") if last_payment else "No Payment Yet",
#                     "parent_contact": getattr(student, 'parent_phone', 'N/A'),
#                 })

#         # 4. Pagination
#         page = self.paginate_queryset(pending_list)
#         if page is not None:
#             return self.get_paginated_response(page)

#         return Response(pending_list)



from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import FeePayment, FeeCategory, FeeStructure
from .serializers import (
   FeePaymentSerializer,
   FeeEntrySerializer,
   FeeCategorySerializer
)
from .pagination import FinancePagination

class FeeCollectionViewSet(viewsets.ModelViewSet):
   """
   Advanced Multi-Tenant Fee Management System:
   - Automatic School Isolation (via school_id or School-ID)
   - Combined Report for Flutter (Summary + Transactions)
   - Dynamic Pending Dues Calculation
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

   # ────────────────────────────────────────────────
   # 🛠️ HELPER: Get School ID (Supports both formats)
   # ────────────────────────────────────────────────
   def _get_school_id(self, request):
       """Dono hyphen (-) aur underscore (_) headers ko handle karta hai"""
       return request.headers.get('school_id') or request.headers.get('School-ID')

   def get_queryset(self):
       """School-ID ke basis par data filter karta hai"""
       school_id = self._get_school_id(self.request)
       if school_id:
           return self.queryset.filter(student__organization_id=school_id)
       return self.queryset.none()

   def get_serializer_class(self):
       if self.action == 'collect':
           return FeeEntrySerializer
       return FeePaymentSerializer

   # ────────────────────────────────────────────────
   # 📊 COMBINED FINANCE REPORT (Matches Flutter Model)
   # ────────────────────────────────────────────────
   @action(detail=False, methods=['get'], url_path='report')
   def get_report(self, request):
       """Flutter FinanceReportData model ke liye single endpoint"""
       school_id = self._get_school_id(request)
       if not school_id:
           return Response({"error": "school_id header is required!"}, status=status.HTTP_400_BAD_REQUEST)

       # Date Filters
       from_date = request.query_params.get('from_date')
       to_date = request.query_params.get('to_date')

       qs = self.get_queryset()
       if from_date and to_date:
           qs = qs.filter(date__date__range=[from_date, to_date])

       # Summary Aggregations
       today = timezone.now().date()
       stats = qs.aggregate(
           total_sum=Sum('amount'),
           online=Sum('amount', filter=Q(payment_mode='Online')),
           offline=Sum('amount', filter=Q(payment_mode='Offline')),
           count=Count('id')
       )
       today_total = qs.filter(date__date=today).aggregate(Sum('amount'))['amount__sum'] or 0

       # Matches FinanceSummaryModel keys exactly
       summary_data = {
           "today_collection": float(today_total),
           "month_collection": float(stats['total_sum'] or 0),
           "pending_dues": 0.0, # Placeholder
           "online_collection": float(stats['online'] or 0),
           "offline_collection": float(stats['offline'] or 0),
           "total_transactions": int(stats['count'] or 0),
       }

       # Transactions List (Matches FinanceTransactionModel)
       transactions_data = []
       for txn in qs.order_by('-date')[:50]:
           transactions_data.append({
               "student_name": txn.student.user.get_full_name(),
               "class_name": f"{txn.student.current_standard.name if txn.student.current_standard else 'N/A'}",
               "amount": float(txn.amount),
               "payment_mode": txn.payment_mode,
               "transaction_id": txn.receipt_no or str(txn.id),
               "date": txn.date.strftime("%d-%b-%Y"), # Format: 12-Aug-2025
           })

       return Response({"summary": summary_data, "transactions": transactions_data})

   # ────────────────────────────────────────────────
   # 💰 SECURE COLLECTION
   # ────────────────────────────────────────────────
   @action(detail=False, methods=['post'], url_path='collect')
   @transaction.atomic
   def collect(self, request):
       """Secure fee entry with user audit trail"""
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

   # ────────────────────────────────────────────────
   # 🕵️ PENDING DUES
   # ────────────────────────────────────────────────
   @action(detail=False, methods=['get'], url_path='pending-dues')
   def pending_dues(self, request):
       """Structure vs Payments compare karke defaulters nikalta hai"""
       school_id = self._get_school_id(request)
       if not school_id:
           return Response({"error": "school_id header is required!"}, status=status.HTTP_400_BAD_REQUEST)

       from students.models import StudentProfile
       students = StudentProfile.objects.filter(organization_id=school_id, is_active=True).select_related('user', 'current_standard')

       pending_list = []
       for student in students:
           structure = FeeStructure.objects.filter(standard=student.current_standard).first()
           if not structure: continue

           total_paid = FeePayment.objects.filter(student=student, status='SUCCESS').aggregate(Sum('amount'))['amount__sum'] or 0
           if total_paid < structure.amount:
               last_payment = FeePayment.objects.filter(student=student).order_by('-date').first()
               pending_list.append({
                   "student_id": str(student.id),
                   "name": student.user.get_full_name(),
                   "class_name": student.current_standard.name if student.current_standard else "N/A",
                   "due_amount": float(structure.amount - total_paid),
                   "last_paid_date": last_payment.date.strftime("%d-%b-%Y") if last_payment else "No Payment Yet",
                   "parent_contact": getattr(student, 'parent_phone', 'N/A'),
               })

       page = self.paginate_queryset(pending_list)
       if page is not None:
           return self.get_paginated_response(page)
       return Response(pending_list)

   # ────────────────────────────────────────────────
   # 📜 HISTORY & CATEGORIES
   # ────────────────────────────────────────────────
   @action(detail=True, methods=['get'], url_path='history')
   def student_history(self, request, pk=None):
       """Individual student ki payment history"""
       history = self.get_queryset().filter(student_id=pk).order_by('-date')
       page = self.paginate_queryset(history)
       if page is not None:
           return self.get_paginated_response(self.get_serializer(page, many=True).data)
       return Response(self.get_serializer(history, many=True).data)

   @action(detail=False, methods=['get'])
   def categories(self, request):
       """Dropdowns ke liye non-paginated categories"""
       self.pagination_class = None
       serializer = FeeCategorySerializer(FeeCategory.objects.all(), many=True)
       return Response(serializer.data)

