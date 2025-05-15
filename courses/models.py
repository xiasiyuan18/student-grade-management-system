from django.db import models

# Create your models here.
from departments.models import Department
from users.models import Teacher

class Course(models.Model):
    """
    存储课程基本信息 (Stores basic course information)
    """
    课程编号 = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name='课程编号',
        help_text='课程的唯一编号，作为主键'
    )
    课程名称 = models.CharField(
        max_length=150,
        null=False,
        blank=False,
        verbose_name='课程名称',
        help_text='课程的完整名称'
    )
    课程说明 = models.TextField(
        null=True,
        blank=True,
        verbose_name='课程说明',
        help_text='课程的详细说明'
    )
    学时 = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='学时',
        help_text='课程的总学时'
    )
    学分 = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        verbose_name='学分',
        help_text='课程的学分'
    )
    学位等级_choices = [
        ('学士', '学士'),
        ('硕士', '硕士'),
        ('博士', '博士'),
    ]
    学位等级 = models.CharField(
        max_length=20,
        choices=学位等级_choices,
        null=True,
        blank=True,
        verbose_name='学位等级',
        help_text='课程适用的学位等级 (如 本科, 硕士, 博士)'
    )
    开课院系编号 = models.ForeignKey(
        Department, # Assuming the Department model is named 'Department'
        on_delete=models.RESTRICT,
        related_name='offered_courses',
        verbose_name='开课院系编号',
        help_text='开设该课程的院系编号'
    )

    class Meta:
        verbose_name = '课程'
        verbose_name_plural = '课程'
        
    def __str__(self):
        return f"{self.课程名称} ({self.课程编号})"

class TeachingAssignment(models.Model):
    """
    记录教师、课程、学期之间的授课关系 (M:N) (Records the teaching relationship between teachers, courses, and semesters (M:N))
    """
    教师工号 = models.ForeignKey(
        Teacher, 
        on_delete=models.RESTRICT,
        verbose_name='教师工号',
        help_text='关联教师表的工号'
    )
    课程编号 = models.ForeignKey(
        Course,
        on_delete=models.RESTRICT,
        verbose_name='课程编号',
        help_text='关联课程表的编号'
    )
    学期 = models.CharField(
        max_length=50,
        verbose_name='学期',
        help_text='授课发生的学期，例如 2024 Fall'
        
    )

    class Meta:
        unique_together = (('教师工号', '课程编号', '学期'),)
        verbose_name = '教师授课'
        verbose_name_plural = '教师授课'

    def __str__(self):
        return f"{self.教师工号} teaches {self.课程编号} in {self.学期}"
