from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

# --- 1. 自定义用户管理器 (CustomUserManager) ---
class CustomUserManager(BaseUserManager):
    """
    为 CustomUser 模型定制的用户管理器。
    """
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError(_('用户必须提供用户名'))
        
        role = extra_fields.pop('role', CustomUser.Role.STUDENT)
        user = self.model(username=username, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields['role'] = CustomUser.Role.ADMIN

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('超级用户必须将 is_staff 设置为 True。'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('超级用户必须将 is_superuser 设置为 True。'))

        return self.create_user(username, password, **extra_fields)


# --- 2. 统一的自定义用户模型 (CustomUser) ---
class CustomUser(AbstractUser):
    """
    统一的自定义用户模型。
    通过 'role' 字段来区分学生、教师和管理员。
    """
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', _('学生')
        TEACHER = 'TEACHER', _('教师')
        ADMIN = 'ADMIN', _('管理员')

    role = models.CharField(
        _('角色'), max_length=10, choices=Role.choices, default=Role.STUDENT
    )
    objects = CustomUserManager()

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = _('系统用户')
        verbose_name_plural = _('系统用户')


# --- 3. 学生 Profile 模型 ---
class Student(models.Model):
    """
    学生 Profile 模型，存储学生特有的信息。
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='student_profile',
        verbose_name=_('关联用户账户')
    )
    student_id_num = models.CharField(
        verbose_name=_('学号'), max_length=50, unique=True
    )
    name = models.CharField(verbose_name=_('姓名'), max_length=100)
    id_card = models.CharField(
        max_length=18, 
        unique=True, 
        null=True,      # ✅ 允许数据库中为 NULL
        blank=True,     # ✅ 允许表单中为空
        verbose_name="身份证号",
        help_text="18位身份证号，可选填"
    )
    
    GENDER_CHOICES = [
        ("男", "男"),
        ("女", "女"),
    ]
    gender = models.CharField(_("性别"), max_length=2, choices=GENDER_CHOICES)
    
    birth_date = models.DateField(_("出生日期"), blank=True, null=True)
    phone = models.CharField(
        max_length=20, 
        null=True, 
        blank=True, 
        verbose_name="联系电话"
    )
    home_address = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="家庭住址"
    )
    dormitory = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name="宿舍信息"
    )
    grade_year = models.IntegerField(_("年级/入学年份"), blank=True, null=True)
    
    # ✨ 主修相关
    major = models.ForeignKey(
        "departments.Major", 
        on_delete=models.PROTECT, 
        verbose_name=_("主修专业"),
        related_name="major_students"
    )
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.PROTECT,
        verbose_name=_("主修院系"),
        related_name="major_department_students"
    )
    
    # ✨ 辅修相关（新增）
    minor_major = models.ForeignKey(
        "departments.Major",
        on_delete=models.SET_NULL,
        verbose_name=_("辅修专业"),
        blank=True,
        null=True,
        related_name="minor_students"
    )
    minor_department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        verbose_name=_("辅修院系"),
        blank=True,
        null=True,
        related_name="minor_department_students"
    )
    
    degree_level = models.CharField(_("学位等级"), max_length=20)
    credits_earned = models.DecimalField(
        _("主修已修学分"), max_digits=5, decimal_places=1, default=0.0  # ✅ 修改为更准确的描述
    )
    
    # ✨ 新增：辅修学分
    minor_credits_earned = models.DecimalField(
        _("辅修已修学分"), max_digits=5, decimal_places=1, default=0.0
    )
    def calculate_cumulative_gpa(self):
        """计算并返回该学生的累计GPA"""
        # 预加载相关数据，提高效率
        grades = self.grades_received.filter(gpa__isnull=False).select_related(
            'teaching_assignment__course'
        )

        total_credit_points = Decimal("0.0")
        total_credits = Decimal("0.0")

        if not grades.exists():
            return Decimal("0.0")

        for grade in grades:
            # 确保课程和学分存在
            course = grade.course
            if course and course.credits:
                credits = Decimal(course.credits)
                if credits > 0:
                    total_credit_points += grade.gpa * credits
                    total_credits += credits
        
        if total_credits == 0:
            return Decimal("0.0")
        
        # 返回最终的累计GPA，保留两位小数
        return round(total_credit_points / total_credits, 2)

    def __str__(self):
        return f"{self.name or self.user.username} (学号: {self.student_id_num})"

    class Meta:
        verbose_name = _('学生档案')
        verbose_name_plural = _('学生档案')
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # 确保主修院系与主修专业匹配
        if self.major and self.department:
            if self.major.department != self.department:
                raise ValidationError({
                    'department': '主修院系必须与主修专业所属院系一致'
                })
        
        # 确保辅修院系与辅修专业匹配
        if self.minor_major and self.minor_department:
            if self.minor_major.department != self.minor_department:
                raise ValidationError({
                    'minor_department': '辅修院系必须与辅修专业所属院系一致'
                })
        
        # 确保主修和辅修不同
        if self.minor_major and self.major:
            if self.minor_major == self.major:
                raise ValidationError({
                    'minor_major': '辅修专业不能与主修专业相同'
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


# --- 4. 教师 Profile 模型 ---
class Teacher(models.Model):
    """
    教师 Profile 模型，存储教师特有的信息。
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='teacher_profile',
        verbose_name=_('关联用户账户')
    )
    teacher_id_num = models.CharField(
        verbose_name=_('教师工号'), max_length=50, unique=True
    )
    name = models.CharField(verbose_name=_('教师姓名'), max_length=100)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        verbose_name=_('所属院系'),
    )

    def __str__(self):
        return f"{self.name or self.user.username} (工号: {self.teacher_id_num})"

    class Meta:
        verbose_name = _('教师档案')
        verbose_name_plural = _('教师档案')