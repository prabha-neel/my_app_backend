from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import AdminProfileSerializer
from rest_framework.throttling import ScopedRateThrottle

class MyProfileView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'profile_api'
    """
    Industry Standard Profile View:
    - Auto-detects role and returns relevant data.
    - Optimized database queries.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Performance optimization: Profile aur Org ko ek sath uthao
        # Note: 'school_admin_profile' Related Name hai jo NormalUser se link hai
        user_with_data = (
            request.user.__class__.objects
            .prefetch_related('school_admin_profile__organization')
            .get(id=user.id)
        )

        if user.role == 'SCHOOL_ADMIN':
            serializer = AdminProfileSerializer(user_with_data)
        else:
            # Baaki roles (Teacher/Student) ke liye hum baad mein serializers add karenge
            return Response({"success": False, "message": "Profile type not supported yet."}, status=400)

        return Response({
            "success": True,
            "message": "Profile fetched successfully",
            "data": serializer.data
        })

    def patch(self, request):
        """Admin apni basic details update kar sakta hai"""
        serializer = AdminProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "data": serializer.data})
        return Response({"success": False, "errors": serializer.errors}, status=400)