from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Grade

@receiver(post_save, sender=Grade)
def update_student_credits_on_grade_save(sender, instance, **kwargs):
    """成绩保存后自动更新学生学分"""
    if instance.student and instance.score is not None:
        from common.views import calculate_and_update_student_credits
        calculate_and_update_student_credits(instance.student)

@receiver(post_delete, sender=Grade)
def update_student_credits_on_grade_delete(sender, instance, **kwargs):
    """成绩删除后自动更新学生学分"""
    if instance.student:
        from common.views import calculate_and_update_student_credits
        calculate_and_update_student_credits(instance.student)