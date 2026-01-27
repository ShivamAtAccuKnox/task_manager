from django.db import models
from django.conf import settings
import uuid


class Project(models.Model):
    project_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_projects")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

class ProjectMember(models.Model):
    project = models.ForeignKey(Project, related_name="members", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="project_memberships")
    
    class Meta:
        unique_together = ['project', 'user']

class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ONGOING = "ONGOING", "Ongoing"
        COMPLETED = "COMPLETED", "Completed"

    task_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50)
    description = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_tasks")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks') 
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,blank=True,null=True,related_name="assigned_tasks")

    def __str__(self) -> str:
        return self.title