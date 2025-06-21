from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Grade
from .services import calculate_and_update_student_credits 

@receiver([post_save, post_delete], sender=Grade)
def trigger_credit_recalculation(sender, instance, **kwargs):
    """
    当一个成绩被保存或删除时，触发学生学分重新计算。
    """
    # instance 是 Grade 对象，从中获取学生 profile
    student_profile = instance.student
    calculate_and_update_student_credits(student_profile)