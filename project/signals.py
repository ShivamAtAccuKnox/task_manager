from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache

# Use relative imports to be safe
from .models import Task, Project
from .tasks import send_email_task

@receiver(post_save, sender=User)
def trigger_welcome_email(sender, instance, created, **kwargs):
    if created and instance.email:
        # Check if we have a default email set, otherwise this might fail silently
        if settings.DEFAULT_FROM_EMAIL:
            send_email_task.delay(
                "Welcome to Task Manager!",
                f"Hi {instance.username}, thanks for joining our platform!",
                [instance.email]
            )

@receiver(pre_save, sender=Task)
def track_task_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_task = Task.objects.get(pk=instance.pk)
            instance._status_changed = (old_task.status != instance.status)
            instance._old_status = old_task.status
        except Task.DoesNotExist:
            instance._status_changed = False
    else:
        instance._status_changed = False

@receiver(post_save, sender=Task)
def notify_status_change_background(sender, instance, created, **kwargs):
    if not created and getattr(instance, '_status_changed', False):
        # Notify the Creator that the status changed
        recipient = instance.created_by.email
        
        # Optional: If the creator changed it, maybe notify the assignee?
        # For now, let's keep your logic (Notify Creator).
        
        if recipient:
            subject = f"Task Updated: {instance.title}"
            message = (
                f"Hello {instance.created_by.username},\n\n"
                f"The status of your task '{instance.title}' has changed.\n"
                f"Old Status: {getattr(instance, '_old_status', 'Unknown')}\n"
                f"New Status: {instance.status}\n"
                f"Project: {instance.project.name}"
            )
            send_email_task.delay(subject, message, [recipient])

@receiver([post_save, post_delete], sender=Task)
def invalidate_task_cache(sender, instance, **kwargs):
    cache.delete_pattern("*task_list*")
    cache.delete_pattern("*project_list*")

@receiver([post_save, post_delete], sender=Project)
def invalidate_project_cache(sender, instance, **kwargs):
    cache.delete_pattern("*projects*")