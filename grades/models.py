from django.conf import settings
from django.db import models
from decimal import Decimal 
from django.core.validators import MinValueValidator, MaxValueValidator
from courses.models import TeachingAssignment 
from users.models import Student 


class Grade(models.Model):
    """成绩模型"""
    
    student = models.ForeignKey(
        Student, 
        on_delete=models.PROTECT, 
        verbose_name='学生',
        related_name='grades_received' 
    )

    teaching_assignment = models.ForeignKey(
        TeachingAssignment, 
        on_delete=models.PROTECT, 
        verbose_name="授课安排",
    )

    score = models.DecimalField(
        verbose_name="分数",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="百分制分数，保留两位小数",
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('100.0'))]
    )

    gpa = models.DecimalField(
        verbose_name='绩点',
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="根据分数自动计算的绩点"
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

    @property
    def term(self):
        if self.teaching_assignment:
            return self.teaching_assignment.semester
        return None

    @property
    def course(self):
        if self.teaching_assignment:
            return self.teaching_assignment.course
        return None

    @property
    def teacher(self):
        if self.teaching_assignment:
            return self.teaching_assignment.teacher
        return None

    def __str__(self):
        student_display = str(self.student)
        assignment_display = str(self.teaching_assignment)
        score_display = str(self.score) if self.score is not None else "未录入"
        return f"{student_display} - {assignment_display}: {score_display}"

    def save(self, *args, **kwargs):
        if self.score is not None:
            # 绩点计算逻辑
            if self.score >= 90:
                self.gpa = Decimal('4.0')
            elif self.score >= 85:
                self.gpa = Decimal('3.7')
            elif self.score >= 80:
                self.gpa = Decimal('3.3')
            elif self.score >= 75:
                self.gpa = Decimal('3.0')
            elif self.score >= 70:
                self.gpa = Decimal('2.7')
            elif self.score >= 65:
                self.gpa = Decimal('2.3')
            elif self.score >= 60:
                self.gpa = Decimal('2.0')
            else:
                self.gpa = Decimal('0.0')
        else:
            self.gpa = None 
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "成绩"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=["student", "teaching_assignment"], 
                name="unique_student_teaching_assignment_grade",
            )
        ]
        ordering = [
            "student",
            "teaching_assignment__semester",
            "teaching_assignment__course__course_name",
        ]