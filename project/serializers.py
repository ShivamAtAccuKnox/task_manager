from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Task, Project,ProjectMember


# --- USER SERIALIZER ---
class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="This email is already in use.")]
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
    

class UserProfileSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(format="%Y-%m-%d")
    active_tasks_count = serializers.SerializerMethodField()
    projects_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined', 'active_tasks_count', 'projects_count']
        read_only_fields = ['date_joined']

    def get_active_tasks_count(self, user):
        return Task.objects.filter(
            project__owner=user, 
            status__in=[Task.Status.PENDING, Task.Status.ONGOING]
        ).count()

    def get_projects_count(self, user):
        return Project.objects.filter(owner=user).count()
    

class DashboardStatsSerializer(serializers.Serializer):
    """
    serializer that accepts a User instance as input 
    and returns calculated dashboard data.
    """
    total_projects = serializers.SerializerMethodField()
    total_tasks = serializers.SerializerMethodField()
    tasks_by_status = serializers.SerializerMethodField()
    overdue_tasks = serializers.SerializerMethodField()


    def get_total_projects(self, user):
        return Project.objects.filter(owner=user).count()

    def get_total_tasks(self, user):
        return Task.objects.filter(project__owner=user).count()

    def get_tasks_by_status(self, user):
        return {
            "pending": Task.objects.filter(project__owner=user, status=Task.Status.PENDING).count(),
            "ongoing": Task.objects.filter(project__owner=user, status=Task.Status.ONGOING).count(),
            "completed": Task.objects.filter(project__owner=user, status=Task.Status.COMPLETED).count(),
        }

    def get_overdue_tasks(self, user):
        return Task.objects.filter(
            project__owner=user,
            deadline__lt=timezone.now(),
            status__in=[Task.Status.PENDING, Task.Status.ONGOING]
        ).count()


# --- TASK SERIALIZER ---
class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    assigned_to_username = serializers.ReadOnlyField(source='assigned_to.username')

    class Meta:
        model = Task
        fields = (
            'task_id', 
            'title', 
            'description', 
            'status', 
            'deadline', 
            'project', 
            'project_name',
            'assigned_to',
            'created_by_username',
            'assigned_to_username'
        )
        read_only_fields = ('task_id', 'created_by_username','assigned_to_username') 

    def create(self, validated_data):
        created_by = self.context['request'].user
        validated_data['created_by'] = created_by

        if not validated_data.get('assigned_to'):
            validated_data['assigned_to'] = created_by
        return super().create(validated_data)

    def validate_deadline(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Deadline cannot be in the past.")
        return value
    
    def validate(self, data):
        """
        Check if the assignee is actually allowed to be on this project.
        """
        assignee = data.get('assigned_to')
        project = data.get('project')
        
        if assignee and project:
            is_member = ProjectMember.objects.filter(project=project, user=assignee).exists()
            is_owner = project.owner == assignee
            if not (is_member or is_owner):
                raise serializers.ValidationError("Assigned user must be a member of the project.")
        return data


# --- PROJECT SERIALIZER ---

class ProjectSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Project
        fields = ['project_id', 'name', 'owner_name']
        read_only_fields = ['project_id']

class ProjectDetailSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['project_id', 'name', 'owner','tasks']
        read_only_fields = ['project_id']


class ProjectMemberSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = ProjectMember
        fields = ['id', 'project', 'user', 'username', 'email']