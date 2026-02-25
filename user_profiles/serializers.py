from rest_framework import serializers
from normal_user.models import NormalUser
from organizations.serializers import OrganizationDetailSerializer

class AdminProfileSerializer(serializers.ModelSerializer):
    # School ki list nest karenge
    organization_list = serializers.SerializerMethodField()
    
    class Meta:
        model = NormalUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 
            'mobile', 'role', 'gender', 'bloodgroup', 'dob', 
            'address', 'admin_custom_id', 'organization_list'
        ]
        read_only_fields = ['id', 'username', 'role', 'admin_custom_id']

    def get_organization_list(self, obj):
        # Admin ke saare profiles uthao (Hamesha List bhejenge)
        profiles = obj.school_admin_profile.select_related('organization').all()
        orgs = [p.organization for p in profiles]
        
        # 'many=True' se hamesha Array [] jayega, chahe 1 school ho ya 5
        return OrganizationDetailSerializer(orgs, many=True).data