from django.contrib.auth.models import (AbstractUser, BaseUserManager, Group,
                                        Permission)
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# 确保 Department 和 Major 模型定义在 'departments.models'
# from departments.models import Department, Major # 如果需要直接类型提示或在 Manager 中使用


# --- 1. 自定义用户管理器 (CustomUserManager) ---
class CustomUserManager(BaseUserManager):
    """
    自定义用户管理器，用于 AUTH_USER_MODEL = CustomUser
    """

    def create_user(
        self, username, email=None, password=None, role=None, **extra_fields
    ):
        if not username:
            raise ValueError(_("用户必须设置用户名"))
        email = self.normalize_email(email)
        # 如果 role 是创建用户时的必需字段，可以在这里处理
        if role:
            extra_fields.setdefault("role", role)

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        
        # ✨ 核心修正：强制将超级用户的角色设置为 ADMIN
        extra_fields.setdefault(
            "role", CustomUser.Role.ADMIN
        )

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("超级用户必须将 is_staff 设置为 True。"))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("超级用户必须将 is_superuser 设置为 True。"))

        return self.create_user(username, email, password, **extra_fields)


# --- 2. 统一的自定义用户模型 (CustomUser) ---
class CustomUser(AbstractUser):
    """
    统一的自定义用户模型。
    学生、教师、管理员都基于此模型创建用户账户。
    登录凭证是 username 和 password (AbstractUser 默认)。
    """

    class Role(models.TextChoices):
        STUDENT = "STUDENT", _("学生")
        TEACHER = "TEACHER", _("教师")
        ADMIN = "ADMIN", _("管理员")

    role = models.CharField(
        _("角色"),
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,  # 新建用户的默认角色是学生
        help_text=_("用户账户的角色类型"),
    )

    # ✨ 关键：将模型与我们上面定义的管理器关联起来
    # 之前这里是被注释掉的，现在我们正式启用它
    objects = CustomUserManager()

    def __str__(self):
        return self.username

    @property
    def student_profile(self):
        """获取学生档案"""
        if self.role == self.Role.STUDENT:
            try:
                # 假设 related_name 是 'student_profile'
                return self.student_profile
            except Student.DoesNotExist:
                return None
        return None

    @property
    def teacher_profile(self):
        """获取教师档案"""
        if self.role == self.Role.TEACHER:
            try:
                # 假设 related_name 是 'teacher_profile'
                return self.teacher_profile
            except Teacher.DoesNotExist:
                return None
        return None

    class Meta:
        verbose_name = _("系统用户")
        verbose_name_plural = _("系统用户")


# --- 3. 学生 Profile 模型 ---
class Student(models.Model):
    """
    学生 Profile 模型，存储学生特有的信息。
    通过 OneToOneField 关联到 CustomUser。
    """

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,  # 将 user 字段设为主键，实现严格的 Profile 模式
        related_name="student_profile",
        verbose_name=_("关联用户账户"),
    )
    student_id_num = models.CharField(  # 学号，作为业务标识符，确保唯一
        verbose_name=_("学号"),
        max_length=50,
        unique=True,
        help_text=_("学生的唯一学号，不同于登录用户名"),
    )
    name = models.CharField(
        verbose_name=_("姓名"),
        max_length=100,
        help_text=_("学生姓名，可以与用户账户名不同"),
    )

    id_card = models.CharField(
        verbose_name=_("身份证号"),
        max_length=18,
        unique=True,
        help_text=_("学生身份证号码"),
    )

    GENDER_CHOICES = [
        ("男", "男"),
        ("女", "女"),
    ]
    gender = models.CharField(
        _("性别"), max_length=2, choices=GENDER_CHOICES, help_text=_("学生性别")
    )
    birth_date = models.DateField(
        _("出生日期"), blank=True, null=True, help_text=_("学生出生日期")
    )
    phone = models.CharField(
        _("电话"), max_length=50, blank=True, null=True, help_text=_("学生联系电话")
    )
    dormitory = models.CharField(
        _("宿舍"), max_length=100, blank=True, null=True, help_text=_("学生住宿信息")
    )
    home_address = models.CharField(
        _("家庭地址"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("学生家庭住址"),
    )
    grade_year = models.IntegerField(
        _("年级/入学年份"), blank=True, null=True, help_text=_("学生入学年份")
    )  # 原 grade 字段

    major = models.ForeignKey(
        "departments.Major",
        on_delete=models.PROTECT,
        verbose_name=_("专业"),
        null=False,
        blank=False,
        help_text=_("学生主修专业"),
    )
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.PROTECT,
        verbose_name=_("主修院系"),
        null=False,
        blank=False,
        related_name="major_department_students",
        help_text=_("学生行政院系"),
    )
    minor_department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        verbose_name=_("辅修院系"),
        blank=True,
        null=True,
        related_name="minor_department_students",
        help_text=_("学生辅修院系"),
    )
    degree_level = models.CharField(
        _("学位等级"), max_length=20, help_text=_("学生当前学位等级")
    )
    credits_earned = models.DecimalField(
        _("已修学分"),
        max_digits=5,
        decimal_places=1,
        default=0.0,
        help_text=_("学生已获得的学分"),
    )

    def __str__(self):
        return f"{self.name or self.user.username} (学号: {self.student_id_num})"

    class Meta:
        verbose_name = _("学生档案")
        verbose_name_plural = _("学生档案")


# --- 4. 教师 Profile 模型 ---
class Teacher(models.Model):
    """
    教师 Profile 模型，存储教师特有的信息。
    通过 OneToOneField 关联到 CustomUser。
    """

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="teacher_profile",
        verbose_name=_("关联用户账户"),
    )
    teacher_id_num = models.CharField(
        verbose_name=_("教师工号"),
        max_length=50,
        unique=True,
        help_text=_("教师的唯一工号，不同于登录用户名"),
    )
    name = models.CharField(
        verbose_name=_("教师姓名"),
        max_length=100,
        help_text=_("教师姓名，可以与用户账户名不同"),
    )

    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.PROTECT,
        verbose_name=_("所属院系"),
        help_text=_("教师所属的行政院系"),
    )

    def __str__(self):
        return f"{self.name or self.user.username} (工号: {self.teacher_id_num})"

    class Meta:
        verbose_name = _("教师档案")
        verbose_name_plural = _("教师档案")
