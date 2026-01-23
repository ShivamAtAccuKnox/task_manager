from django.db.models.signals import pre_save, post_save,post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth.models import User
from project.models import Task,Project
from .tasks import send_welcome_email_task
from django.core import cache
    

@receiver(post_save, sender=User)
def trigger_welcome_email(sender, instance, created, **kwargs):
    if created:
        send_welcome_email_task.delay(instance.email, instance.username)


@receiver(pre_save, sender=Task)
def track_task_status_change(sender, instance, **kwargs):
    """
    Check if the status is changing before the model is saved.
    We store a temporary flag on the instance to check later in post_save.
    """
    # If the task is new (no primary key yet), it's being created, not updated.
    if instance.pk is None:
        instance._status_changed = False
        return

    try:
        # Fetch the 'old' object currently in the database
        old_task = Task.objects.get(pk=instance.pk)
        
        # Compare old status vs new status
        if old_task.status != instance.status:
            instance._status_changed = True
            instance._old_status = old_task.status  # Store old status for the email msg
        else:
            instance._status_changed = False
            
    except Task.DoesNotExist:
        # Should not happen given the pk check, but good for safety
        instance._status_changed = False

@receiver(post_save, sender=Task)
def send_email_on_status_change(sender, instance, created, **kwargs):
    """
    Send the email only if the status actually changed.
    """
    # Check the flag we set in pre_save. 
    # We use getattr() to avoid errors if the flag wasn't set (e.g. on creation)
    if not created and getattr(instance, '_status_changed', False):
        
        subject = f"Task Updated: {instance.title}"
        message = (
            f"Hello {instance.created_by.username},\n\n"
            f"The status of your task '{instance.title}' has changed.\n"
            f"Old Status: {getattr(instance, '_old_status', 'Unknown')}\n"
            f"New Status: {instance.status}\n\n"
            f"Project: {instance.project.name}"
        )
        
        print(f"📧 Sending email for task {instance.title}...") # Debug print
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.created_by.email],
            fail_silently=False,
        )