from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from .models import SchoolNote, SchoolAsset
from .serializers import SchoolNoteSerializer, SchoolAssetSerializer
from organizations.models import Organization, SchoolAdmin

class SchoolNoteListCreateView(generics.ListCreateAPIView):
    serializer_class = SchoolNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Logic: User ya toh Org ka main Admin ho, ya SchoolAdmin profile mein ho
        return SchoolNote.objects.filter(
            Q(organization__admin=user) | 
            Q(organization__school_admins__user=user)
        ).distinct().exclude(status='COMPLETED')

    def perform_create(self, serializer):
        user = self.request.user
        # Org dhoondo jahan user Admin ya SchoolAdmin hai
        org = Organization.objects.filter(
            Q(admin=user) | 
            Q(school_admins__user=user)
        ).first()

        if not org:
            raise ValidationError("Bhai, ye user kisi bhi school/organization se linked nahi hai.")
        
        serializer.save(author=user, organization=org)

class SchoolAssetListCreateView(generics.ListCreateAPIView):
    serializer_class = SchoolAssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return SchoolAsset.objects.filter(
            Q(organization__admin=user) | 
            Q(organization__school_admins__user=user)
        ).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        org = Organization.objects.filter(
            Q(admin=user) | 
            Q(school_admins__user=user)
        ).first()

        if not org:
            raise ValidationError("Asset add karne ke liye organization nahi mili.")
        
        serializer.save(organization=org)