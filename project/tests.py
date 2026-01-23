from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.test import override_settings
from project.models import Project, Task

User = get_user_model()

# This decorator disables caching for all tests in this file.
# It prevents "Admin" results from leaking into "Owner" tests.
@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
class BaseViewTest(APITestCase):
    
    def setUp(self):
        # 1. Create Users
        self.admin = User.objects.create_superuser(username='admin', email='admin@test.com', password='pwd')
        self.owner = User.objects.create_user(username='owner', email='owner@test.com', password='pwd')
        self.stranger = User.objects.create_user(username='stranger', email='stranger@test.com', password='pwd')

        # 2. Create Data belonging to 'owner'
        self.project = Project.objects.create(name="Owner Project", owner=self.owner)
        self.task = Task.objects.create(
            title="Owner Task", 
            description="Desc",
            project=self.project,
            created_by=self.owner,
            deadline=timezone.now() + timedelta(days=1),
            status="PENDING"
        )
        
        # 3. Create Data belonging to 'stranger'
        self.stranger_project = Project.objects.create(name="Stranger Project", owner=self.stranger)

    def get_results(self, response):
        """Helper to handle pagination."""
        if 'results' in response.data:
            return response.data['results']
        return response.data


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
class ProjectViewSetTests(BaseViewTest):

    def setUp(self):
        super().setUp()
        self.list_url = reverse('project-list')
        self.detail_url = reverse('project-detail', args=[self.project.project_id])

    # ------------------------------------------------
    # 1. GET (List)
    # ------------------------------------------------
    def test_list_projects_authenticated(self):
        """Owner should see ONLY their 1 project."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = self.get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Owner Project")

    def test_list_projects_stranger(self):
        """Stranger should see ONLY their 1 project."""
        self.client.force_authenticate(user=self.stranger)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = self.get_results(response)
        self.assertEqual(len(results), 1) 
        self.assertEqual(results[0]['name'], "Stranger Project")

    def test_list_projects_admin(self):
        """Admin should see ALL projects (2 total)."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = self.get_results(response)
        self.assertEqual(len(results), 2)

    # ------------------------------------------------
    # 2. GET (Retrieve Detail)
    # ------------------------------------------------
    def test_retrieve_project_owner(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Owner Project")

    def test_retrieve_project_stranger(self):
        """Stranger tries to access Owner's specific project ID."""
        self.client.force_authenticate(user=self.stranger)
        response = self.client.get(self.detail_url)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

    # ------------------------------------------------
    # 3. POST (Create)
    # ------------------------------------------------
    def test_create_project_owner(self):
        self.client.force_authenticate(user=self.owner)
        data = {"name": "New Owner Project"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.filter(owner=self.owner).count(), 2)


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
class TaskViewSetTests(BaseViewTest):
    
    def setUp(self):
        super().setUp()
        self.list_url = reverse('task-list')
        self.detail_url = reverse('task-detail', args=[self.task.task_id])

    # ------------------------------------------------
    # 1. GET (List)
    # ------------------------------------------------
    def test_list_tasks_owner(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 1)

    def test_list_tasks_stranger(self):
        self.client.force_authenticate(user=self.stranger)
        response = self.client.get(self.list_url)
        results = self.get_results(response)
        # Stranger has 0 tasks initially
        self.assertEqual(len(results), 0)

    # ------------------------------------------------
    # 2. CREATE (Security Check)
    # ------------------------------------------------
    def test_create_task_in_own_project(self):
        self.client.force_authenticate(user=self.owner)
        data = {
            "title": "New Task",
            "description": "Desc",
            "deadline": timezone.now() + timedelta(days=1),
            "project": self.project.project_id,
            "status": "PENDING"
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_task_in_strangers_project(self):
        """
        CRITICAL: Owner tries to assign a task to Stranger's project.
        """
        self.client.force_authenticate(user=self.owner)
        data = {
            "title": "Malicious Task",
            "description": "Desc",
            "deadline": timezone.now() + timedelta(days=1),
            "project": self.stranger_project.project_id, # INVALID
            "status": "PENDING"
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------
    # 3. DELETE
    # ------------------------------------------------
    def test_delete_task_owner(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_task_stranger(self):
        self.client.force_authenticate(user=self.stranger)
        response = self.client.delete(self.detail_url)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])