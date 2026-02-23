from rest_framework import permissions

class IsSchoolAdmin(permissions.BasePermission):
    """
    Sirf wahi user access kar paye jiska role SCHOOL_ADMIN ho.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'SCHOOL_ADMIN'
        )