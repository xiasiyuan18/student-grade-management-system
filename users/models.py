from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class StudentManager(BaseUserManager):
    def create_user(self, student_id, password=None, **extra_fields):
        """
        创建并保存一个具有给定学号和密码的学生用户。
        """
        if not student_id:
            raise ValueError('学生必须有一个学号')
        student = self.model(student_id=student_id, **extra_fields)
        student.set_password(password)
        student.save(using=self._db)
        return student

    def create_superuser(self, student_id, password=None, **extra_fields):
        """
        创建并保存一个具有给定学号和密码的超级用户学生。
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须将 is_staff 设置为 True。')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须将 is_superuser 设置为 True。')

        return self.create_user(student_id, password, **extra_fields)

class Student(AbstractBaseUser, PermissionsMixin):
    """
    学生模型
    """
    GENDER_CHOICES = [
        ('男', '男'),
        ('女', '女'),
    ]

    student_id = models.CharField(verbose_name='学号', max_length=50, unique=True, help_text='学生的唯一标识')
    name = models.CharField(verbose_name='姓名', max_length=100, help_text='学生姓名')
    id_card = models.CharField(verbose_name='身份证号', max_length=18, unique=True, help_text='学生身份证号码')
    dormitory = models.CharField(verbose_name='宿舍', max_length=100, blank=True, null=True, help_text='学生住宿信息')
    home_address = models.CharField(verbose_name='家庭地址', max_length=255, blank=True, null=True, help_text='学生家庭住址')
    phone = models.CharField(verbose_name='电话', max_length=50, blank=True, null=True, help_text='学生联系电话')
    birth_date = models.DateField(verbose_name='出生日期', blank=True, null=True, help_text='学生出生日期')
    gender = models.CharField(verbose_name='性别', max_length=2, choices=GENDER_CHOICES, help_text='学生性别')
    grade = models.IntegerField(verbose_name='年级', blank=True, null=True, help_text='学生入学年份')
    major_id = models.IntegerField(verbose_name='专业编号', help_text='学生主修专业编号') # 假设专业是一个独立的模型，这里用ID关联
    department_id = models.IntegerField(verbose_name='主修院系编号', help_text='学生行政院系编号') # 假设院系是一个独立的模型，这里用ID关联
    minor_department_id = models.IntegerField(verbose_name='辅修院系编号', blank=True, null=True, help_text='学生辅修院系编号') # 假设院系是一个独立的模型，这里用ID关联
    degree_level = models.CharField(verbose_name='学位等级', max_length=20, help_text='学生当前学位等级')
    credits_earned = models.DecimalField(verbose_name='已修学分', max_digits=5, decimal_places=1, default=0.0, help_text='学生已获得的学分')
    # 密码字段由 AbstractBaseUser 提供
    #到时候可以使用set_password方法来设置密码.check_password方法来验证密码

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) # 普通学生不是教职工

    objects = StudentManager()

    USERNAME_FIELD = 'student_id' # 使用学号作为登录用户名
    REQUIRED_FIELDS = ['name', 'id_card', 'gender', 'major_id', 'department_id', 'degree_level'] # 创建超级用户时必须填写的字段

    class Meta:
        verbose_name = '学生'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name
    




from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# 假设 Department 模型将会在 'departments' app 中定义由成员A负责
# from departments.models import Department # 最终需要取消注释并确保路径正确

class TeacherManager(BaseUserManager):
    def create_user(self, teacher_id, password=None, **extra_fields):
        """
        创建并保存一个具有给定工号和密码的教师用户。
        """
        if not teacher_id:
            raise ValueError('教师必须有一个工号 (teacher_id)')

        name = extra_fields.pop('name', None)
        if not name:
            raise ValueError('创建教师用户时必须提供姓名 (name)')

        department = extra_fields.pop('department', None)
        if not department:
            # 假设调用者会传入 Department 实例，或者你需要在这里根据 department_id 查找
            raise ValueError('创建教师用户时必须提供所属院系 (department)')
        # 如果 department 是 department_id, 则需要:
        # try:
        #     DepartmentModel = self.model._meta.get_field('department').remote_field.model
        #     department_instance = DepartmentModel.objects.get(pk=department) # 假设 department 变量存的是ID
        # except DepartmentModel.DoesNotExist:
        #     raise ValueError('提供的院系ID无效')
        # department = department_instance # 现在 department 是 Department 实例

        teacher = self.model(
            teacher_id=teacher_id,
            name=name,
            department=department,
            **extra_fields
        )
        teacher.set_password(password) # 哈希密码
        teacher.save(using=self._db)
        return teacher

    def create_superuser(self, teacher_id, password=None, **extra_fields):
        """
        创建并保存一个具有给定工号和密码的超级用户教师。
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True.')

        return self.create_user(teacher_id, password, **extra_fields)


class Teacher(AbstractBaseUser, PermissionsMixin):
    """
    教师实体模型 (精简版)
    - 教师可查看：工号、姓名、所属院系、可修改：姓名、密码。
    - 工号和院系通常由管理员修改。
    """
    teacher_id = models.CharField(
        verbose_name='教师工号',
        max_length=50,
        unique=True,
        primary_key=True, # 工号作为主键
        help_text='教师的唯一工号，用于登录系统。通常不可由用户自行修改。'
    )
    name = models.CharField(
        verbose_name='教师姓名',
        max_length=100,
        help_text='教师的真实姓名。允许教师自行修改。'
    )

    department = models.ForeignKey(
        'departments.Department', # 指向成员A定义的Department模型
        on_delete=models.PROTECT,
        verbose_name='所属院系',
        null=False, # 教师必须属于一个院系
        blank=False,
        help_text='教师所属的行政院系。通常由管理员进行调整。'
    )

    # 密码字段由 AbstractBaseUser 隐式提供和管理
    # 教师可以通过特定接口修改自己的密码

    # --- Django用户模型所需的核心字段 ---
    is_active = models.BooleanField(
        default=True,
        help_text='指定此用户是否被视为活动状态。'
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='指定用户是否可以登录到此站点的管理后台。'
    )
    # is_superuser 字段由 PermissionsMixin 提供

    date_joined = models.DateTimeField(
        verbose_name='加入日期',
        default=timezone.now,
        help_text='用户账户创建的日期和时间'
    )

    objects = TeacherManager()

    USERNAME_FIELD = 'teacher_id'
    REQUIRED_FIELDS = ['name', 'department'] # 创建用户时（尤其superuser）必需的字段

    class Meta:
        verbose_name = '教师'
        verbose_name_plural = '教师'
        ordering = ['teacher_id']

    def __str__(self):
        return f"{self.name} ({self.teacher_id})"

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name