from django.contrib import admin
from .models import Project, Task, ProjectMember

class ProjectMemberInline(admin.TabularInline):
    """
    Allows you to add Members directly inside the Project screen.
    """
    model = ProjectMember
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    inlines = [ProjectMemberInline]

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'assigned_to', 'deadline')
    list_filter = ('status', 'project')

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'project')
    list_filter = ('project',)