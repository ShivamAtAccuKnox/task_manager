from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import Task

@shared_task
def send_welcome_email_task(email, username):
    """
    Sends a welcome email to new users.
    """
    subject = 'Welcome to Task Manager!'
    message = f'Hi {username}, thanks for registering on our platform.'
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    return f"Welcome email sent to {email}"


@shared_task(name="check_deadlines_and_notify")
def check_deadlines_and_notify():
    """
    Checks for tasks due in the next 24 hours and sends reminders.
    """
    now = timezone.now()
    next_24_hours = now + timedelta(hours=24)

    # 1. Query: Find tasks due soon that are not completed
    # Note: We use 'created_by' because that is the field in your Task model.
    tasks_due_soon = Task.objects.filter(
        deadline__gt=now,                 # Strictly in the future
        deadline__lte=next_24_hours,      # Within 24 hours
        status__in=['PENDING', 'ONGOING'] # Not completed
    ).select_related('created_by', 'project') # Optimization to fetch user/project in one query

    emails_sent = 0

    for task in tasks_due_soon:
        user = task.created_by  # <--- FIXED: Changed from assigned_to to created_by
        
        if not user.email:
            continue 

        subject = f"Deadline Reminder: {task.title}"
        message = (
            f"Hi {user.username},\n\n"
            f"This is a reminder that the task '{task.title}' in project '{task.project.name}' "
            f"is due on {task.deadline.strftime('%Y-%m-%d %H:%M')}.\n\n"
            f"Current Status: {task.get_status_display()}\n"
            f"Please update it soon!"
        )

        try:
            print(f"📧 Sending reminder for {task.title} to {user.email}...")
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            emails_sent += 1
        except Exception as e:
            print(f"Error sending email to {user.email}: {e}")

    return f"Checked Deadlines. Sent {emails_sent} reminders."