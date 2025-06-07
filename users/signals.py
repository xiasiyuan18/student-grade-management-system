"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Student, Teacher

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == User.Role.STUDENT:
            if not hasattr(instance, 'student_profile'):
                Student.objects.create(user=instance)
        elif instance.role == User.Role.TEACHER:
            if not hasattr(instance, 'teacher_profile'):
                Teacher.objects.create(user=instance)
"""