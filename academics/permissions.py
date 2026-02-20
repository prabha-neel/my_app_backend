from rest_framework import permissions

class IsSchoolAdmin(permissions.BasePermission):
    """
    Sirf wahi user access kar payega jiska role 'SCHOOL_ADMIN' hai.
    """
    def has_permission(self, request, view):
        # Pehle check karo user logged in hai aur uska role admin hai
        return bool(
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'role', None) == 'SCHOOL_ADMIN'
        )

class IsOrganizationOwner(permissions.BasePermission):
    """
    Check karta hai ki kya Admin usi Organization ka owner hai jiska data wo bhej raha hai.
    """
    def has_object_permission(self, request, view, obj):
        # obj yahan Organization ka instance hoga
        return obj.admin == request.user