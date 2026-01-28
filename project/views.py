from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db.models import Q # <--- NEEDED for "Owner OR Member" logic
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Task, Project, ProjectMember
from .serializers import (
    TaskSerializer, ProjectSerializer, UserSerializer,
    ProjectDetailSerializer, DashboardStatsSerializer,
    UserProfileSerializer, ProjectMemberSerializer
)
# Ensure your permissions.py allows members to read, or switch to IsAuthenticated
from .permissions import IsOwnerOrAdmin 

# Filters
from .filters import TaskFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    # Switched to IsAuthenticated so Members can view. 
    # (You can enforce Owner-only edit in the Permission class itself)
    permission_classes = [permissions.IsAuthenticated] 
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    # @method_decorator(cache_page(60 * 15, key_prefix="project_list"))
    # @method_decorator(vary_on_headers("Authorization"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Logic Update: Show projects where User is Owner OR Member
        """
        user = self.request.user
        queryset = Project.objects.prefetch_related('tasks')

        if user.is_staff:
            return queryset
        
        # Q(owner=user) -> Projects I own
        # Q(members__user=user) -> Projects I am a member of
        return queryset.filter(Q(owner=user) | Q(members__user=user)).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectSerializer

    # --- NEW: MEMBER MANAGEMENT ACTIONS ---

    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        """
        POST /api/projects/{id}/add-member/
        """
        project = self.get_object()
        
        # Optional: Security check (Only Owner can add members)
        if project.owner != request.user and not request.user.is_staff:
             return Response({"detail": "Only the Project Owner can add members."}, status=403)

        serializer = ProjectMemberSerializer(data=request.data)
        if serializer.is_valid():
            user_to_add = serializer.validated_data['user']
            
            # Check for duplicates
            if ProjectMember.objects.filter(project=project, user=user_to_add).exists():
                return Response({"error": "User is already a member."}, status=400)
            
            # Save with project context
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """
        GET /api/projects/{id}/members/
        """
        project = self.get_object()
        members = ProjectMember.objects.filter(project=project)
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated] # Simplified for now
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['deadline']
    ordering = ['created_at']

    # @method_decorator(cache_page(60 * 15, key_prefix='task_list'))
    # @method_decorator(vary_on_headers("Authorization"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """
        Logic Update: Show tasks from projects where User is Owner OR Member
        """
        user = self.request.user
        
        if user.is_staff:
            return Task.objects.all()
        
        # Filter tasks where the parent project involves the user
        return Task.objects.filter(
            Q(project__owner=user) | Q(project__members__user=user)
        ).distinct()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_create(self, serializer):
        # We rely on Serializer 'create' method for assignment logic, 
        # but we need to ensure created_by is set.
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        serializer = DashboardStatsSerializer(instance=request.user)
        return Response(serializer.data)