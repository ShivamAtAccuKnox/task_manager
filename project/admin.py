from django.contrib import admin

# Register your models here.
from project.models import Project,Task

admin.site.register(Project)
admin.site.register(Task)