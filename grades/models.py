# grades/models.py
from django.conf import settings
from django.db import models

# from courses.models import Course # 不再直接关联 Course
from courses.models import TeachingAssignment  # 直接关联 TeachingAssignment
from users.models import Student

# from users.models import Teacher # 不再直接关联 Teacher


class Grade(models.Model):
    """
    成绩模型
    关联到学生和具体的授课安排 (TeachingAssignment)
    """

    student = models.ForeignKey(Student, on_delete=models.PROTECT, verbose_name="学生")
    teaching_assignment = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.PROTECT,  # 如果一个授课安排有成绩了，不应轻易删除
        verbose_name="授课安排",
    )
    score = models.DecimalField(
        verbose_name="分数",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="百分制分数，保留两位小数",
    )
    entry_time = models.DateTimeField(
        verbose_name="录入时间", auto_now_add=True, help_text="成绩首次录入系统的时间"
    )
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="modified_grades",
        verbose_name="最后修改人",
    )
    last_modified_time = models.DateTimeField(
        verbose_name="最后修改时间", auto_now=True
    )

    # term 字段现在可以从 self.teaching_assignment.semester 获取
    # course 字段可以从 self.teaching_assignment.course 获取
    # teacher 字段可以从 self.teaching_assignment.teacher 获取

    class Meta:
        verbose_name = "成绩"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "teaching_assignment",
                ],  # 一个学生在一个授课安排下只有一条成绩记录
                name="unique_student_teaching_assignment_grade",
            )
        ]
        ordering = [
            "student",
            "teaching_assignment__semester",
            "teaching_assignment__course__course_name",
        ]

    def __str__(self):
        student_display = str(self.student)
        assignment_display = str(self.teaching_assignment)
        score_display = str(self.score) if self.score is not None else "未录入"
        return f"{student_display} - {assignment_display}: {score_display}"

    # 可以在这里添加一个 property 来方便地获取 term, course, teacher
    @property
    def term(self):
        return self.teaching_assignment.semester

    @property
    def course(self):
        return self.teaching_assignment.course

    @property
    def teacher(self):
        return self.teaching_assignment.teacher
