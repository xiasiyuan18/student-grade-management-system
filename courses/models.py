from decimal import Decimal

from django.core.validators import (MaxValueValidator, MinLengthValidator,
                                    MinValueValidator, RegexValidator)
from django.db import models

# 假设 Department 模型定义在 departments.models 中
# from departments.models import Department # 如果跨 app 引用，确保 app 在 INSTALLED_APPS 且路径正确

# 假设 Teacher 模型定义在 users.models 中
# from users.models import Teacher


class Course(models.Model):
    """
    存储课程基本信息
    对应 SQL 表: 课程
    学时将通过学分动态计算 (学时 = 学分)
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
        null=True,
        blank=True,
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
        null=True,
        blank=True,
        help_text="课程适用的学位等级 (可选)",
    )
    department = models.ForeignKey(
        "departments.Department",  # 使用字符串引用
        on_delete=models.PROTECT,
        verbose_name="开课院系",
        help_text="开设该课程的院系",
    )

    @property
    def course_hours(self):
        """动态计算学时，这里简单认为学时等于学分。"""
        return self.credits  # 因为老师说一学分对应一学时

    # 如果需要在 Admin 后台也方便地显示这个计算出来的学时
    def display_course_hours(self):
        return self.course_hours

    display_course_hours.short_description = "学时 (计算所得)"  # Admin 中显示的列名

    def __str__(self):
        return f"{self.course_id} - {self.course_name}"

    class Meta:
        verbose_name = "课程"
        verbose_name_plural = "课程"


# TeachingAssignment 模型定义保持不变 (因为它不直接依赖学时字段)
# ... (TeachingAssignment 模型代码，如果与 Course 在同一个文件) ...


class TeachingAssignment(models.Model):
    """
    记录教师、课程、学期之间的授课关系 (M:N)
    对应 SQL 表: 教师授课
    这是 Teacher 和 Course 之间的多对多关系的中间表，并带有额外字段 '学期'
    """

    teacher = models.ForeignKey(
        "users.Teacher", on_delete=models.PROTECT, verbose_name="授课教师"
    )
    course = models.ForeignKey(
        Course,  # 关联到上面定义的 Course 模型
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
        )  # 避免在 teacher 未加载时出错
        course_str = (
            str(self.course) if self.course_id else "未知课程"
        )  # 避免在 course 未加载时出错
        return f"{teacher_str} - {course_str} ({self.semester})"

    class Meta:
        verbose_name = "教师授课安排"
        verbose_name_plural = "教师授课安排"
        unique_together = ("teacher", "course", "semester")
