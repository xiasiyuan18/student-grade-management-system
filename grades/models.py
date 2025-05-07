from django.db import models
from django.conf import settings # 用于关联自定义用户模型

# 假设你的 Student 用户模型在 'users' 应用中
# from users.models import Student (settings.AUTH_USER_MODEL 通常就够了)

# 假设你的 Course 模型在 'courses' 应用中
# from courses.models import Course

# 假设你的 Teacher 模型在 'teachers' 应用中 (或者 'users' 应用)
# from teachers.models import Teacher

class Grade(models.Model):
    """
    成绩模型
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, # 指向 'users.Student'
        on_delete=models.CASCADE,
        verbose_name='学生'
    )

    course = models.ForeignKey(
        'courses.Course', # 字符串形式 'app_label.ModelName'
        on_delete=models.CASCADE, # 或 PROTECT，取决于业务逻辑，课程被删除成绩是否保留
        verbose_name='课程'
    )

    # 授课教师工号(外键关联教师表)
    # 假设你在 'teachers' 应用中定义了 Teacher 模型
    # 或者如果 Teacher 模型在 'users' 应用中，就是 'users.Teacher'
    teacher = models.ForeignKey(
        'teachers.Teacher', # <--- 修改点: 明确为外键, 指向 Teacher 模型
        on_delete=models.SET_NULL, # 教师被删除，成绩中的教师信息设为NULL，或 PROTECT
        null=True, # 允许为NULL，如果on_delete=SET_NULL
        # blank=True, # 根据图片，它是主键的一部分，所以理论上不应为 null/blank，
                      # 但如果on_delete=SET_NULL则必须允许null。
                      # 如果联合主键字段不允许NULL，那么on_delete不能是SET_NULL。
                      # 这需要你根据实际业务确定：如果教师是联合主键一部分，是否能被删除？
                      # 如果教师被删除，对应成绩如何处理？通常PROTECT更合适。
                      # 若用PROTECT, 则null=False, blank=False (默认)
        verbose_name='授课教师'
    )
    # 如果教师是 'users' 应用中的模型，例如 class Teacher(models.Model):
    # teacher = models.ForeignKey('users.Teacher', on_delete=models.SET_NULL, null=True, verbose_name='授课教师')

    term = models.CharField(
        verbose_name='学期',
        max_length=50,
        help_text='成绩对应的学期，例如 "2024-2025第一学期"'
    )

    score = models.DecimalField(
        verbose_name='分数',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='百分制分数，保留两位小数'
    )

    entry_time = models.DateTimeField(
        verbose_name='录入时间',
        auto_now_add=True,
        help_text='成绩录入系统的时间'
    )

    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, # 操作者是系统用户
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_grades',
        verbose_name='最后修改人',
        help_text='最后修改此成绩记录的用户'
    )

    last_modified_time = models.DateTimeField(
        verbose_name='最后修改时间',
        auto_now=True,
        help_text='成绩记录最后修改的时间'
    )

    class Meta:
        verbose_name = '成绩'
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course', 'teacher', 'term'], # <--- 修改点: 使用 teacher 外键字段
                name='unique_student_course_teacher_term_grade'
            )
        ]
        # ordering = ['student', 'term', 'course']

    def __str__(self):
        student_name = self.student.name if self.student and hasattr(self.student, 'name') else str(self.student_id)
        course_name = self.course.name if self.course and hasattr(self.course, 'name') else str(self.course_id)
        teacher_name = self.teacher.name if self.teacher and hasattr(self.teacher, 'name') else str(self.teacher_id) # 假设 Teacher 模型有 name 属性
        score_display = self.score if self.score is not None else '未录入'
        return f"{student_name} - {course_name} - (教师: {teacher_name}) - {self.term}: {score_display}"