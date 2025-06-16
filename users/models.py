from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


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
    id_card = models.CharField(verbose_name=_('身份证号'), max_length=18, unique=True)
    
    # ✨ 关键修复：重新添加 GENDER_CHOICES 和 gender 字段
    GENDER_CHOICES = [
        ("男", "男"),
        ("女", "女"),
    ]
    gender = models.CharField(_("性别"), max_length=2, choices=GENDER_CHOICES)
    
    birth_date = models.DateField(_("出生日期"), blank=True, null=True)
    phone = models.CharField(_("电话"), max_length=50, blank=True, null=True)
    dormitory = models.CharField(_("宿舍"), max_length=100, blank=True, null=True)
    home_address = models.CharField(_("家庭地址"), max_length=255, blank=True, null=True)
    grade_year = models.IntegerField(_("年级/入学年份"), blank=True, null=True)
    major = models.ForeignKey(
        "departments.Major", on_delete=models.PROTECT, verbose_name=_("专业")
    )
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.PROTECT,
        verbose_name=_("主修院系"),
        related_name="major_department_students"
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
        _("已修学分"), max_digits=5, decimal_places=1, default=0.0
    )

    def __str__(self):
        return f"{self.name or self.user.username} (学号: {self.student_id_num})"

    class Meta:
        verbose_name = _('学生档案')
        verbose_name_plural = _('学生档案')


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