from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, ProjectViewSet,UserProfileView

# Create Router
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/me/', UserProfileView.as_view(), name='user_profile'),
]