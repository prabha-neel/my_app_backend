from rest_framework import serializers
from .models import SchoolNote, SchoolAsset

class SchoolNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.first_name')
    
    class Meta:
        model = SchoolNote
        fields = '__all__'
        read_only_fields = ['author', 'organization']

class SchoolAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolAsset
        fields = '__all__'
        read_only_fields = ['organization']