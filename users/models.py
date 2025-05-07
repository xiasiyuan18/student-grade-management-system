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