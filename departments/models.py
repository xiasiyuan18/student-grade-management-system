# departments/models.py

from decimal import Decimal

from django.core.validators import (MinLengthValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models


class Department(models.Model):
    """
    存储院系基本信息
    对应 SQL 表: 院系
    """

    # 院系编号 (id): Django 会自动创建一个名为 id 的自增主键字段，
    # 这对应 SQL 中的 `院系编号 int NOT NULL AUTO_INCREMENT PRIMARY KEY`。
    # 因此我们通常不在模型中显式定义这个主键字段。

    dept_code = models.CharField(
        verbose_name="院系代码",  # 在 Admin 后台等处显示的名称
        max_length=20,  # 对应 varchar(20)
        unique=True,  # 对应 UNIQUE KEY `uq_院系代码`
        null=False,  # 对应 NOT NULL (CharField/TextField 默认值)
        blank=False,  # Django 表单验证，不允许为空字符串
        validators=[
            MinLengthValidator(
                2
            )  # 对应 CHECK (length(`院系代码`) between 2 and 20) 的下限
            # max_length=20 隐含了长度上限
        ],
        help_text="院系的对外代码，唯一，例如 CS, MATH (2-20字符)",  # 帮助提示文本
        # db_comment="院系的对外代码，如 CS, MATH" # Django 4.2+ 可以直接添加数据库注释
    )

    dept_name = models.CharField(
        verbose_name="院系名称",
        max_length=25,  # 对应 varchar(25)
        unique=True,  # 对应 UNIQUE KEY `uq_院系名称`
        null=False,  # 对应 NOT NULL
        blank=False,  # 对应 CHECK (trim(`院系名称`) <> '')，确保不为空
        help_text="院系的完整名称，唯一",
        # db_comment="院系的完整名称"
    )

    office_location = models.CharField(
        verbose_name="办公地点",
        max_length=30,  # 对应 varchar(30)
        null=True,  # 对应 DEFAULT NULL，允许数据库存储 NULL
        blank=True,  # 允许在表单中留空
        help_text="院系办公地点 (可选)",
        # db_comment="院系办公地点"
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
        # db_comment="院系联系电话"
    )

    def __str__(self):
        """返回院系名称作为对象的字符串表示，方便在Admin后台等处识别。"""
        return self.dept_name

    class Meta:
        """模型的元数据选项"""

        verbose_name = "院系"  # 在 Admin 后台等显示的单数名称
        verbose_name_plural = (
            "院系"  # 在 Admin 后台等显示的复数名称 (中文通常单复数相同)
        )
        # db_table_comment = "存储院系基本信息" # Django 5.0+ 可以直接添加表注释


class Major(models.Model):
    """
    存储专业信息及其与院系的关系
    对应 SQL 表: 专业
    """

    # 专业编号 (id): Django 自动处理，对应 AUTO_INCREMENT PRIMARY KEY

    major_name = models.CharField(
        verbose_name="专业名称",
        max_length=100,
        null=False,
        blank=False,  # 对应 CHECK (trim(`专业名称`) <> '')
        help_text="专业的完整名称",
        # db_comment="专业的完整名称"
    )

    # 所属院系编号: 外键关联到 Department 模型
    department = models.ForeignKey(
        Department,  # 直接引用同文件中的 Department 类
        on_delete=models.PROTECT,  # 对应 ON DELETE RESTRICT (PROTECT更符合Django习惯)
        # PROTECT 防止删除还有专业关联的院系
        null=False,  # 对应 NOT NULL
        verbose_name="所属院系",
        help_text="该专业所属（开设）的院系",
        # db_column='所属院系编号' # (可选) 如果你想让数据库列名保持中文，但不推荐
        # related_name='majors' # (可选) 用于从 Department 对象反向查询其所有 Major
        # db_comment="该专业所属（开设）院系的编号"
    )

    bachelor_credits_required = models.DecimalField(
        verbose_name="学士学分要求",
        max_digits=5,  # 对应 decimal(5, 1)
        decimal_places=1,
        default=Decimal("0.0"),  # 对应 DEFAULT '0.0'，使用 Decimal 类型
        validators=[MinValueValidator(Decimal("0.0"))],  # 对应 CHECK (学分要求 >= 0)
        help_text="完成该专业学士学位所需的最低学分 (>=0)",
        # db_comment="完成该专业学士学位所需的最低学分"
    )

    master_credits_required = models.DecimalField(
        verbose_name="硕士学分要求",
        max_digits=5,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0"))],
        help_text="完成该专业硕士学位所需的最低学分 (>=0)",
        # db_comment="完成该专业硕士学位所需的最低学分"
    )

    doctor_credits_required = models.DecimalField(
        verbose_name="博士学分要求",
        max_digits=5,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0"))],
        help_text="完成该专业博士学位所需的最低学分 (>=0)",
        # db_comment="完成该专业博士学位所需的最低学分"
    )

    def __str__(self):
        """返回 专业名称(所属院系名称) 作为对象的字符串表示"""
        # 为了区分不同院系下的同名专业，最好加上院系信息
        return f"{self.major_name} ({self.department.dept_name})"  # 假设 Department 有 dept_name 字段

    class Meta:
        verbose_name = "专业"
        verbose_name_plural = "专业"
        # 对应 UNIQUE KEY `uq_专业名称_所属院系` (`专业名称`, `所属院系编号`)
        unique_together = ("major_name", "department")
        # db_table_comment = "存储专业信息及其与院系的关系" # Django 5.0+
