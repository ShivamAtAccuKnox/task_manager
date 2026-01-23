import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from faker import Faker

# Replace 'your_app_name' with the actual name of your app
from project.models import Project, Task

class Command(BaseCommand):
    help = 'Populates the database with fake data for Users, Projects, and Tasks'

    def handle(self, *args, **kwargs):
        fake = Faker()
        User = get_user_model()
        
        self.stdout.write('Seeding data...')

        # Use atomic transaction to ensure data integrity and speed
        with transaction.atomic():
            # 1. Create 10 Users
            for _ in range(10):
                username = fake.unique.user_name()
                email = fake.unique.email()
                
                # Simple check to prevent duplicate errors if running multiple times
                if User.objects.filter(username=username).exists():
                    continue

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='password123' # Default password for testing
                )

                self.stdout.write(f'Created User: {user.username}')

                # 2. Create Projects for this User (Random 1 to 3 projects)
                for _ in range(random.randint(1, 3)):
                    project = Project.objects.create(
                        name=fake.catch_phrase(), # Generates "Business-focused" names
                        owner=user
                    )

                    # 3. Create Tasks for this Project (Random 3 to 6 tasks)
                    for _ in range(random.randint(3, 6)):
                        # CONSTRAINT MET HERE: 
                        # We use the same 'user' variable for created_by that we used for the project owner.
                        Task.objects.create(
                            project=project,
                            created_by=user, 
                            title=fake.sentence(nb_words=4).rstrip('.'),
                            description=fake.text(max_nb_chars=200),
                            status=random.choice(Task.Status.choices)[0], # Picks 'PENDING', 'ONGOING', etc.
                            deadline=fake.future_datetime(end_date='+30d', tzinfo=timezone.get_current_timezone())
                        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database with 10 users, projects, and tasks!'))