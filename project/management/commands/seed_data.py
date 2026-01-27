import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from faker import Faker

from project.models import Project, Task, ProjectMember

class Command(BaseCommand):
    help = 'Populates the database with fake data for Users, Projects, and Tasks'

    def handle(self, *args, **kwargs):
        fake = Faker()
        User = get_user_model()
        
        self.stdout.write('Seeding data...')

        with transaction.atomic():
            # 1. Create 15 Users to have a good pool for memberships
            all_users = []
            for _ in range(15):
                username = fake.unique.user_name()
                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(
                        username=username,
                        email=fake.unique.email(),
                        password='password123'
                    )
                    all_users.append(user)
            
            self.stdout.write(f'Created {len(all_users)} Users.')

            # 2. Create Projects
            for user in all_users[:5]:  # Let's make the first 5 users "Project Owners"
                for _ in range(random.randint(1, 2)):
                    project = Project.objects.create(
                        name=fake.catch_phrase(),
                        owner=user
                    )

                    # 3. Add Members to the Project
                    # Pick 3-5 random users (excluding the owner) to be members
                    potential_members = [u for u in all_users if u != user]
                    assigned_members = random.sample(potential_members, k=random.randint(3, 5))
                    
                    member_objs = []
                    for member in assigned_members:
                        member_objs.append(ProjectMember(project=project, user=member))
                    
                    ProjectMember.objects.bulk_create(member_objs)

                    # 4. Create Tasks for this Project
                    # Pool of people who can be assigned: Owner + Members
                    eligible_assignees = assigned_members + [user]

                    for _ in range(random.randint(4, 8)):
                        creator = random.choice(eligible_assignees)
                        assignee = random.choice(eligible_assignees)

                        Task.objects.create(
                            project=project,
                            created_by=creator,
                            assigned_to=assignee, # Now follows business logic!
                            title=fake.sentence(nb_words=4).rstrip('.'),
                            description=fake.text(max_nb_chars=200),
                            status=random.choice(Task.Status.choices)[0],
                            deadline=fake.future_datetime(end_date='+30d', tzinfo=timezone.get_current_timezone())
                        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database with Users, Projects, Members, and Tasks!'))