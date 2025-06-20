import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dept_code', models.CharField(help_text='院系的对外代码，唯一，例如 CS, MATH (2-20字符)', max_length=20, unique=True, validators=[django.core.validators.MinLengthValidator(2)], verbose_name='院系代码')),
                ('dept_name', models.CharField(help_text='院系的完整名称，唯一', max_length=25, unique=True, verbose_name='院系名称')),
                ('office_location', models.CharField(blank=True, help_text='院系办公地点 (可选)', max_length=30, null=True, verbose_name='办公地点')),
                ('phone_number', models.CharField(blank=True, help_text='院系联系电话 (可选, 6-20位数字/+/ -)', max_length=20, null=True, validators=[django.core.validators.RegexValidator(message='电话号码格式不正确，应为6-20位的数字、+ 或 -', regex='^[0-9+-]{6,20}$')], verbose_name='联系电话')),
            ],
            options={
                'verbose_name': '院系',
                'verbose_name_plural': '院系',
            },
        ),
        migrations.CreateModel(
            name='Major',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('major_name', models.CharField(help_text='专业的完整名称', max_length=100, verbose_name='专业名称')),
                ('major_code', models.CharField(blank=True, help_text='专业的唯一代码，例如：CS001, MATH002', max_length=20, null=True, unique=True, verbose_name='专业代码')),
                ('degree_type', models.CharField(choices=[('bachelor', '学士'), ('master', '硕士'), ('doctor', '博士'), ('all', '本硕博')], default='bachelor', help_text='该专业提供的学位类型', max_length=20, verbose_name='学位类型')),
                ('duration', models.CharField(choices=[('2', '2年'), ('3', '3年'), ('4', '4年'), ('5', '5年'), ('6', '6年')], default='4', help_text='该专业的标准学制年限', max_length=10, verbose_name='学制')),
                ('description', models.TextField(blank=True, help_text='专业的详细描述和培养目标（可选）', max_length=500, null=True, verbose_name='专业描述')),
                ('bachelor_credits_required', models.DecimalField(decimal_places=1, default=Decimal('0.0'), help_text='完成该专业学士学位所需的最低学分 (>=0)', max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.0'))], verbose_name='学士学分要求')),
                ('master_credits_required', models.DecimalField(decimal_places=1, default=Decimal('0.0'), help_text='完成该专业硕士学位所需的最低学分 (>=0)', max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.0'))], verbose_name='硕士学分要求')),
                ('doctor_credits_required', models.DecimalField(decimal_places=1, default=Decimal('0.0'), help_text='完成该专业博士学位所需的最低学分 (>=0)', max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.0'))], verbose_name='博士学分要求')),
                ('department', models.ForeignKey(help_text='该专业所属（开设）的院系', on_delete=django.db.models.deletion.PROTECT, to='departments.department', verbose_name='所属院系')),
            ],
            options={
                'verbose_name': '专业',
                'verbose_name_plural': '专业',
                'unique_together': {('major_name', 'department')},
            },
        ),
    ]
