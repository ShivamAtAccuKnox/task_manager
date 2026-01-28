from rest_framework import permissions
from .models import Project, Task

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom Permission:
    - Admin: Full Access.
    - Project Owner: Full Access to Project and its Tasks.
    - Project Member: Read Only on Project; Edit Access on assigned Tasks.
    """
    def has_object_permission(self, request, view, obj):
        # 1. Admin : Allow everything
        if request.user.is_staff or request.user.is_superuser:
            return True

        # --- PROJECT LEVEL PERMISSIONS ---
        if isinstance(obj, Project):
            # Owners can do anything (Edit, Delete, View)
            if obj.owner == request.user:
                return True
            
            # Members can only View (GET, HEAD, OPTIONS)
            if request.method in permissions.SAFE_METHODS:
                return obj.members.filter(user=request.user).exists()
            
            return False

        # --- TASK LEVEL PERMISSIONS ---
        if isinstance(obj, Task):
            # Project Owner can do anything
            if obj.project.owner == request.user:
                return True

            # Task Creator or Assignee can Edit
            if obj.created_by == request.user or obj.assigned_to == request.user:
                return True
            
            # Other Project Members can only View
            if request.method in permissions.SAFE_METHODS:
                return obj.project.members.filter(user=request.user).exists()
                
            return False

        return False