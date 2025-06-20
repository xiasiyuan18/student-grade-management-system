

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('departments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseEnrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enrollment_date', models.DateTimeField(auto_now_add=True, verbose_name='选课时间')),
                ('status', models.CharField(choices=[('ENROLLED', '已选课'), ('DROPPED', '已退课'), ('COMPLETED', '已完成')], default='ENROLLED', max_length=20, verbose_name='选课状态')),
            ],
            options={
                'verbose_name': '选课记录',
                'verbose_name_plural': '选课记录',
                'ordering': ['-enrollment_date'],
            },
        ),
        migrations.CreateModel(
            name='TeachingAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester', models.CharField(help_text='授课发生的学期，例如 2024 Fall', max_length=50, validators=[django.core.validators.RegexValidator(message="学期格式不正确，应为 'YYYY Season' 例如 '2024 Fall'", regex='^[0-9]{4} (Spring|Fall|Summer|Winter)$')], verbose_name='学期')),
            ],
            options={
                'verbose_name': '教师授课安排',
                'verbose_name_plural': '教师授课安排',
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('course_id', models.CharField(help_text='课程的唯一编号 (3-20字符)', max_length=50, primary_key=True, serialize=False, validators=[django.core.validators.MinLengthValidator(3)], verbose_name='课程编号')),
                ('course_name', models.CharField(help_text='课程的完整名称', max_length=150, verbose_name='课程名称')),
                ('description', models.TextField(blank=True, help_text='课程的详细说明 (可选)', null=True, verbose_name='课程说明')),
                ('credits', models.DecimalField(decimal_places=1, default=Decimal('0.0'), help_text='课程的学分 (0.0-30.0)', max_digits=3, validators=[django.core.validators.MinValueValidator(Decimal('0.0')), django.core.validators.MaxValueValidator(Decimal('30.0'))], verbose_name='学分')),
                ('degree_level', models.CharField(blank=True, choices=[('学士', '学士'), ('硕士', '硕士'), ('博士', '博士')], help_text='课程适用的学位等级 (可选)', max_length=20, null=True, verbose_name='学位等级')),
                ('department', models.ForeignKey(help_text='开设该课程的院系', on_delete=django.db.models.deletion.PROTECT, to='departments.department', verbose_name='开课院系')),
            ],
            options={
                'verbose_name': '课程',
                'verbose_name_plural': '课程',
                'ordering': ['course_id'],
            },
        ),
    ]
