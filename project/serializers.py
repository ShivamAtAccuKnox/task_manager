from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Task, Project
from django.db import transaction


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


# --- TASK SERIALIZER ---
class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    created_by_username = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Task
        fields = ['task_id', 'title', 'description', 'status', 'deadline', 'project', 'project_name', 'created_by_username']
        read_only_fields = ['task_id', 'created_by_username']

    def validate_project(self, project):
        """
        Security Check: Ensure user owns the project they are assigning a task to.
        """
        user = self.context['request'].user
        if user.is_staff or user.is_superuser:
            return project
            
        if project.owner != user:
            raise serializers.ValidationError("You cannot add tasks to a project you do not own.")
        return project

    def validate_deadline(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Deadline cannot be in the past.")
        return value


# --- PROJECT SERIALIZER ---
class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    tasks = TaskSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Project
        fields = ['project_id', 'name', 'owner', 'tasks']
        read_only_fields = ['project_id']