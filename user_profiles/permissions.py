from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Sirf wahi user apna profile dekh sake, ya fir SuperAdmin.
    """
    def has_object_permission(self, request, view, obj):
        # Superuser ko permission hai
        if request.user.is_staff:
            return True
        # User sirf apna data dekh sakta hai
        return obj.id == request.user.id