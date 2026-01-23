from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission:
    - Admins: Can do anything.
    - Users: Can only view/edit their own objects.
    """
    def has_object_permission(self, request, view, obj):
        # 1. Admin Logic: Allow everything
        if request.user.is_staff or request.user.is_superuser:
            return True

        # 2. Normal User Logic: Check ownership
        # Handle Project model (field: 'owner')
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        # Handle Task model (field: 'created_by')
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
            
        return False