from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from rest_framework import viewsets, permissions, generics
from rest_framework.response import Response

from .models import Task, Project
from .serializers import (
    TaskSerializer, ProjectSerializer, UserSerializer,ProjectDetailSerializer,DashboardStatsSerializer,UserProfileSerializer
    )
from .permissions import IsOwnerOrAdmin

# Filters
from .filters import TaskFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from rest_framework.decorators import action


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny] 


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        GET /api/auth/me/
        Returns the profile of the currently logged-in user.
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        """
        PATCH /api/auth/me/
        Allows user to update their own username/email.
        """
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    @method_decorator(cache_page(60 * 15, key_prefix="project_list"))
    @method_decorator(vary_on_headers("Authorization"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        queryset = Project.objects.prefetch_related('tasks')

        if user.is_staff:
            return queryset
        return queryset.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    def get_serializer_class(self):
        """
        Return detailed serializer for 'retrieve' (GET ID),
        and standard serializer for 'list' (GET ALL).
        """
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectSerializer


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_class = TaskFilter
    
    search_fields = ['title', 'description']
    ordering_fields = ['deadline']
    ordering = ['created_at']

    @method_decorator(cache_page(60 * 15, key_prefix='task_list'))
    @method_decorator(vary_on_headers("Authorization"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return Task.objects.all()
        
        return Task.objects.filter(project__owner=user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        GET /api/tasks/dashboard/
        Returns aggregated statistics for the current user.
        """
        serializer = DashboardStatsSerializer(instance=request.user)
        return Response(serializer.data)
    

