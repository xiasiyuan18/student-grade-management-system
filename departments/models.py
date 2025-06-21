from decimal import Decimal

from django.core.validators import (MinLengthValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models


class Department(models.Model):
    """
    存储院系基本信息
    对应 SQL 表: 院系
    """

    dept_code = models.CharField(
        verbose_name="院系代码",  # 在 Admin 后台等处显示的名称
        max_length=20,  # 对应 varchar(20)
        unique=True,  # 对应 UNIQUE KEY `uq_院系代码`
        null=False,  # 对应 NOT NULL
        blank=False,  # Django 表单验证，不允许为空字符串
        validators=[
            MinLengthValidator(
                2
            )  # 对应 CHECK (length(`院系代码`) between 2 and 20) 的下限
        ],
        help_text="院系的对外代码，唯一，例如 CS, MATH (2-20字符)",  # 帮助提示文本
    )

    dept_name = models.CharField(
        verbose_name="院系名称",
        max_length=25,  # 对应 varchar(25)
        unique=True,  # 对应 UNIQUE KEY `uq_院系名称`
        null=False,  # 对应 NOT NULL
        blank=False,  # 对应 CHECK (trim(`院系名称`) <> '')，确保不为空
        help_text="院系的完整名称，唯一",
    )

    office_location = models.CharField(
        verbose_name="办公地点",
        max_length=30,  # 对应 varchar(30)
        null=True,  # 对应 DEFAULT NULL，允许数据库存储 NULL
        blank=True,  # 允许在表单中留空
        help_text="院系办公地点 (可选)",
    )

    phone_number = models.CharField(
        verbose_name="联系电话",
        max_length=20,  # 对应 varchar(20)
        null=True,  # 对应 DEFAULT NULL
        blank=True,  # 允许在表单中留空
        validators=[
            RegexValidator(
                regex=r"^[0-9+-]{6,20}$",  # 对应 CHECK 约束中的正则表达式
                message="电话号码格式不正确，应为6-20位的数字、+ 或 -",
            )
        ],
        help_text="院系联系电话 (可选, 6-20位数字/+/ -)",
    )

    def __str__(self):
        """返回院系名称作为对象的字符串表示，方便在Admin后台等处识别。"""
        return self.dept_name

    class Meta:
        """模型的元数据选项"""

        verbose_name = "院系"
        verbose_name_plural = (
            "院系"
        )


class Major(models.Model):
    """
    存储专业信息及其与院系的关系
    对应 SQL 表: 专业
    """

    major_name = models.CharField(
        verbose_name="专业名称",
        max_length=100,
        null=False,
        blank=False,
        help_text="专业的完整名称",
    )

    # 专业代码
    major_code = models.CharField(
        verbose_name="专业代码",
        max_length=20,
        unique=True,
        null=True,  # 暂时允许为空，便于迁移
        blank=True,
        help_text="专业的唯一代码，例如：CS001, MATH002",
    )

    # 所属院系编号: 外键关联到 Department 模型
    department = models.ForeignKey(
        Department, 
        on_delete=models.PROTECT,
        null=False,  # 对应 NOT NULL
        verbose_name="所属院系",
        help_text="该专业所属（开设）的院系",
    )

    # 学位类型
    DEGREE_TYPE_CHOICES = [
        ('bachelor', '学士'),
        ('master', '硕士'),
        ('doctor', '博士'),
        ('all', '本硕博'),
    ]
    degree_type = models.CharField(
        verbose_name="学位类型",
        max_length=20,
        choices=DEGREE_TYPE_CHOICES,
        default='bachelor',
        help_text="该专业提供的学位类型",
    )

    # 学制
    DURATION_CHOICES = [
        ('2', '2年'),
        ('3', '3年'),
        ('4', '4年'),
        ('5', '5年'),
        ('6', '6年'),
    ]
    duration = models.CharField(
        verbose_name="学制",
        max_length=10,
        choices=DURATION_CHOICES,
        default='4',
        help_text="该专业的标准学制年限",
    )

    # 专业描述
    description = models.TextField(
        verbose_name="专业描述",
        max_length=500,
        null=True,
        blank=True,
        help_text="专业的详细描述和培养目标（可选）",
    )

    bachelor_credits_required = models.DecimalField(
        verbose_name="学士学分要求",
        max_digits=5,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0"))],
        help_text="完成该专业学士学位所需的最低学分 (>=0)",
    )

    master_credits_required = models.DecimalField(
        verbose_name="硕士学分要求",
        max_digits=5,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0"))],
        help_text="完成该专业硕士学位所需的最低学分 (>=0)",
    )

    doctor_credits_required = models.DecimalField(
        verbose_name="博士学分要求",
        max_digits=5,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0"))],
        help_text="完成该专业博士学位所需的最低学分 (>=0)",
    )

    def __str__(self):
        """返回 专业名称(所属院系名称) 作为对象的字符串表示"""
        return f"{self.major_name} ({self.department.dept_name})"

    class Meta:
        verbose_name = "专业"
        verbose_name_plural = "专业"
        unique_together = ("major_name", "department")