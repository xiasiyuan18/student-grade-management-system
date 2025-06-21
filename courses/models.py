
from decimal import Decimal
from django.core.validators import (MaxValueValidator, MinLengthValidator,
                                    MinValueValidator, RegexValidator)
from django.db import models


from departments.models import Department
from users.models import Teacher, Student


class Course(models.Model):
    """
    存储课程基本信息
    对应 SQL 表: 课程
    """
    course_id = models.CharField(
        verbose_name="课程编号",
        max_length=50,
        primary_key=True,
        validators=[
            MinLengthValidator(3),
        ],
        help_text="课程的唯一编号 (3-20字符)",
    )
    course_name = models.CharField(
        verbose_name="课程名称",
        max_length=150,
        null=False,
        blank=False,
        help_text="课程的完整名称",
    )
    description = models.TextField(
        verbose_name="课程说明",
        blank=True,
        null=True,
        help_text="课程的详细说明 (可选)",
    )
    credits = models.DecimalField(
        verbose_name="学分",
        max_digits=3,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[
            MinValueValidator(Decimal("0.0")),
            MaxValueValidator(Decimal("30.0")),
        ],
        help_text="课程的学分 (0.0-30.0)",
    )
    degree_level_choices = [
        ("学士", "学士"),
        ("硕士", "硕士"),
        ("博士", "博士"),
    ]
    degree_level = models.CharField(
        verbose_name="学位等级",
        max_length=20,
        choices=degree_level_choices,
        blank=True,
        null=True,
        help_text="课程适用的学位等级 (可选)",
    )
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.PROTECT,
        verbose_name="开课院系",
        help_text="开设该课程的院系",
    )

    def __str__(self):
        return f"{self.course_id} - {self.course_name}"

    class Meta:
        verbose_name = "课程"
        verbose_name_plural = "课程"
        ordering = ['course_id']


class TeachingAssignment(models.Model):
    """
    记录教师、课程、学期之间的授课关系 (M:N)
    对应 SQL 表: 教师授课
    """
    teacher = models.ForeignKey(
        "users.Teacher", on_delete=models.PROTECT, verbose_name="授课教师"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        verbose_name="所授课程",
    )
    semester = models.CharField(
        verbose_name="学期",
        max_length=50,
        null=False,
        blank=False,
        validators=[
            RegexValidator(
                regex=r"^[0-9]{4} (Spring|Fall|Summer|Winter)$",
                message="学期格式不正确，应为 'YYYY Season' 例如 '2024 Fall'",
            )
        ],
        help_text="授课发生的学期，例如 2024 Fall",
    )

    def __str__(self):
        teacher_str = (
            str(self.teacher) if self.teacher_id else "未知教师"
        )
        course_str = (
            str(self.course) if self.course_id else "未知课程"
        )
        return f"{teacher_str} - {course_str} ({self.semester})"

    class Meta:
        verbose_name = "教师授课安排"
        verbose_name_plural = "教师授课安排"
        unique_together = ("teacher", "course", "semester")


class CourseEnrollment(models.Model):
    """学生选课记录"""
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        verbose_name='学生',
        related_name='course_enrollments'
    )
    
   
    teaching_assignment = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.CASCADE,
        verbose_name='授课安排',
 
        related_name='enrollments'
    )
    
    enrollment_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='选课时间'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('ENROLLED', '已选课'),
            ('DROPPED', '已退课'),
            ('COMPLETED', '已完成'),
        ],
        default='ENROLLED',
        verbose_name='选课状态'
    )

    class Meta:
        verbose_name = '选课记录'
        verbose_name_plural = verbose_name
        unique_together = ['student', 'teaching_assignment']
        ordering = ['-enrollment_date']

    def __str__(self):
        return f"{self.student.name} - {self.teaching_assignment.course.course_name}"