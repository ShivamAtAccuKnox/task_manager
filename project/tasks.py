from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import Task

@shared_task(name="send_email_task")
def send_email_task(subject, message, recipient_list):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False
        )
        return f"Email sent to {recipient_list}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

@shared_task(name="check_deadlines_and_notify")
def check_deadlines_and_notify():
    """
    Checks for tasks due in the next 24 hours.
    Sends reminder to the ASSIGNEE (or creator if unassigned).
    """
    now = timezone.now()
    next_24_hours = now + timedelta(hours=24)

    tasks_due_soon = Task.objects.filter(
        deadline__gt=now,
        deadline__lte=next_24_hours,
        status__in=['PENDING', 'ONGOING']
    ).select_related('created_by', 'assigned_to', 'project')

    emails_sent = 0

    for task in tasks_due_soon:
        target_user = task.assigned_to if task.assigned_to else task.created_by
        
        if not target_user or not target_user.email:
            continue 

        subject = f"Deadline Reminder: {task.title}"
        message = (
            f"Hi {target_user.username},\n\n"
            f"This is a reminder that the task '{task.title}' in project '{task.project.name}' "
            f"is due on {task.deadline.strftime('%Y-%m-%d %H:%M')}.\n\n"
            f"Current Status: {task.status}\n"
            f"Please update it soon!"
        )

        try:
            send_email_task.delay(subject, message, [target_user.email])
            emails_sent += 1
        except Exception as e:
            print(f"Error queuing email for {target_user.email}: {e}")

    return f"Checked Deadlines. Sent {emails_sent} reminders."