from django.db.models.signals import pre_save, post_save,post_delete
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import User
from project.models import Task,Project
from .tasks import send_email_task
from django.core import cache


@receiver(post_save, sender=User)
def trigger_welcome_email(sender, instance, created, **kwargs):
    if created and instance.email:
        subject = "Welcome to Task Manager!"
        message = f"Hi {instance.username}, thanks for joining our platform!"
        send_email_task.delay(subject, message, [instance.email])


# --- TASK STATUS CHANGE TRACKING ---
@receiver(pre_save, sender=Task)
def track_task_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_task = Task.objects.get(pk=instance.pk)
            if old_task.status != instance.status:
                instance._status_changed = True
                instance._old_status = old_task.status
            else:
                instance._status_changed = False
        except Task.DoesNotExist:
            instance._status_changed = False
    else:
        instance._status_changed = False

@receiver(post_save, sender=Task)
def notify_status_change_background(sender, instance, created, **kwargs):
    """
    Detects status change and sends email via Celery.
    """
    if not created and getattr(instance, '_status_changed', False):
        recipient = instance.created_by.email
        if recipient:
            subject = f"Task Updated: {instance.title}"
            message = (
                f"Hello {instance.created_by.username},\n\n"
                f"The status of your task '{instance.title}' has changed.\n"
                f"Old Status: {getattr(instance, '_old_status', 'Unknown')}\n"
                f"New Status: {instance.status}\n\n"
                f"Project: {instance.project.name}"
            )
            send_email_task.delay(subject, message, [recipient])

@receiver([post_save, post_delete], sender=Task)
def invalidate_task_cache(sender, instance, **kwargs):
    """
    Clears cache whenever a task is Created, Updated, or Deleted.
    """
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern("*task_list*")
        cache.delete_pattern("*project_list*")
    else:
        cache.clear()

@receiver([post_save, post_delete], sender=Project)
def invalidate_project_cache(sender, instance, **kwargs):
    """
    Clears cache whenever a project is Created, Updated, or Deleted.
    """
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern("*projects*")
    else:
        cache.clear()