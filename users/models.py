from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# 确保 Department 和 Major 模型定义在 'departments.models'
# from departments.models import Department, Major # 如果需要直接类型提示或在 Manager 中使用

# --- 1. 自定义用户管理器 (CustomUserManager) ---
# 对于继承自 AbstractUser 的模型，通常可以不自定义 Manager，除非有非常特殊的创建逻辑。
# 如果需要，可以像这样定义：
class CustomUserManager(BaseUserManager):
    """
    自定义用户管理器，用于 AUTH_USER_MODEL = CustomUser
    """
    def create_user(self, username, email=None, password=None, role=None, **extra_fields):
        if not username:
            raise ValueError(_('用户必须设置用户名'))
        email = self.normalize_email(email)
        # 如果 role 是创建用户时的必需字段，可以在这里处理
        if role:
            extra_fields.setdefault('role', role)

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', CustomUser.Role.ADMIN) # 超级用户默认为 ADMIN 角色

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('超级用户必须将 is_staff 设置为 True。'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('超级用户必须将 is_superuser 设置为 True。'))
        
        return self.create_user(username, email, password, **extra_fields)

# --- 2. 统一的自定义用户模型 (CustomUser) ---
class CustomUser(AbstractUser):
    """
    统一的自定义用户模型。
    学生、教师、管理员都基于此模型创建用户账户。
    登录凭证是 username 和 password (AbstractUser 默认)。
    """
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', _('学生')
        TEACHER = 'TEACHER', _('教师')
        ADMIN = 'ADMIN', _('管理员')

    # AbstractUser 已经包含了:
    # username, first_name, last_name, email, password,
    # groups, user_permissions,
    # is_staff, is_active, is_superuser,
    # last_login, date_joined

    role = models.CharField(
        _('角色'),
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT, # 可以根据注册逻辑设置默认角色
        help_text=_('用户账户的角色类型')
    )

    # 如果你想用 email 作为登录凭证，可以在 Meta 中设置 USERNAME_FIELD = 'email'
    # 并将 username 字段的 unique=False, null=True, blank=True （或者直接移除 username 如果不需要）
    # REQUIRED_FIELDS 也要相应调整。
    # 但通常保留 username 用于登录，email 用于通知等，是一个不错的选择。

    # objects = CustomUserManager() # 只有在你定义了上面的 CustomUserManager 并且想用它时才取消注释

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = _('系统用户')
        verbose_name_plural = _('系统用户')

# --- 3. 学生 Profile 模型 ---
class Student(models.Model):
    """
    学生 Profile 模型，存储学生特有的信息。
    通过 OneToOneField 关联到 CustomUser。
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True, # 将 user 字段设为主键，实现严格的 Profile 模式
        related_name='student_profile',
        verbose_name=_('关联用户账户')
    )
    student_id_num = models.CharField( # 学号，作为业务标识符，确保唯一
        verbose_name=_('学号'),
        max_length=50,
        unique=True,
        help_text=_('学生的唯一学号，不同于登录用户名')
    )
    # 如果 CustomUser 中已有 first_name, last_name，这里的 name 可以考虑是否需要
    # 如果需要独立的姓名，可以保留；否则可以通过 user.get_full_name() 获取
    name = models.CharField(verbose_name=_('姓名'), max_length=100, help_text=_('学生姓名，可以与用户账户名不同'))
    
    id_card = models.CharField(verbose_name=_('身份证号'), max_length=18, unique=True, help_text=_('学生身份证号码'))
    
    GENDER_CHOICES = [
        ('男', '男'),
        ('女', '女'),
    ]
    gender = models.CharField(_('性别'), max_length=2, choices=GENDER_CHOICES, help_text=_('学生性别'))
    birth_date = models.DateField(_('出生日期'), blank=True, null=True, help_text=_('学生出生日期'))
    phone = models.CharField(_('电话'), max_length=50, blank=True, null=True, help_text=_('学生联系电话'))
    dormitory = models.CharField(_('宿舍'), max_length=100, blank=True, null=True, help_text=_('学生住宿信息'))
    home_address = models.CharField(_('家庭地址'), max_length=255, blank=True, null=True, help_text=_('学生家庭住址'))
    grade_year = models.IntegerField(_('年级/入学年份'), blank=True, null=True, help_text=_('学生入学年份')) # 原 grade 字段

    major = models.ForeignKey(
        'departments.Major',
        on_delete=models.PROTECT, # 或 SET_NULL, 根据业务逻辑
        verbose_name=_('专业'),
        null=True, blank=True,
        help_text=_('学生主修专业')
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT, # 或 SET_NULL
        verbose_name=_('主修院系'),
        null=True, blank=True,
        related_name='major_department_students',
        help_text=_('学生行政院系')
    )
    minor_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        verbose_name=_('辅修院系'),
        blank=True, null=True,
        related_name='minor_department_students',
        help_text=_('学生辅修院系')
    )
    degree_level = models.CharField(_('学位等级'), max_length=20, help_text=_('学生当前学位等级'))
    credits_earned = models.DecimalField(_('已修学分'), max_digits=5, decimal_places=1, default=0.0, help_text=_('学生已获得的学分'))

    def __str__(self):
        return f"{self.name or self.user.username} (学号: {self.student_id_num})"

    class Meta:
        verbose_name = _('学生档案')
        verbose_name_plural = _('学生档案')

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
        related_name='teacher_profile',
        verbose_name=_('关联用户账户')
    )
    teacher_id_num = models.CharField( # 工号，作为业务标识符，确保唯一
        verbose_name=_('教师工号'),
        max_length=50,
        unique=True,
        help_text=_('教师的唯一工号，不同于登录用户名')
    )
    # name 可以使用 CustomUser 的 first_name, last_name
    # 如果需要独立的姓名，可以保留；否则可以通过 user.get_full_name() 获取
    name = models.CharField(verbose_name=_('教师姓名'), max_length=100, help_text=_('教师姓名，可以与用户账户名不同'))

    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        verbose_name=_('所属院系'),
        # null=False, blank=False, # 如果教师必须属于一个院系
        help_text=_('教师所属的行政院系')
    )
    # is_active, is_staff, date_joined 等信息由 CustomUser 管理

    def __str__(self):
        return f"{self.name or self.user.username} (工号: {self.teacher_id_num})"

    class Meta:
        verbose_name = _('教师档案')
        verbose_name_plural = _('教师档案')