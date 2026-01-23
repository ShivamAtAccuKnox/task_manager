from django.db import models
from django.conf import settings
import uuid

# Create your models here.

class Project(models.Model):
    project_id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="projects")

    def __str__(self) -> str:
        return self.name

class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING" ,"Pending" 
        ONGOING = "ONGOING" ,"Ongoing" 
        COMPLETED = "COMPLETED", "Completed"

    task_id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    description = models.TextField()
    status = models.CharField(max_length=15,choices=Status.choices,default=Status.PENDING)
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title

