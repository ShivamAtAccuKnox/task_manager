import django_filters
from .models import Task

class TaskFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Task.Status.choices)
    
    project = django_filters.UUIDFilter(field_name='project__project_id')
    deadline_after = django_filters.DateTimeFilter(field_name='deadline', lookup_expr='gte')
    deadline_before = django_filters.DateTimeFilter(field_name='deadline', lookup_expr='lte')

    class Meta:
        model = Task
        fields = ['status', 'project', 'deadline_after', 'deadline_before']