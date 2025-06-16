# core/views.py (最终修正版)

import json
from django.db.models import Count, Q
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache

# 导入所有需要的模型
from users.models import CustomUser, Student, Teacher
from departments.models import Department
from grades.models import Grade
from courses.models import Course, TeachingAssignment


class HomeView(LoginRequiredMixin, TemplateView):
    """
    统一的仪表盘主页视图。
    - 总是渲染带图表的 core/home.html 模板。
    - 根据用户角色（管理员、教师、学生）提供不同的数据。
    - 为管理员和教师的仪表盘数据应用缓存，提高性能。
    """

    template_name = "core/home.html"  # 明确指定加载带图表的模板

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # --- 核心修正点 ---
        # 使用最直接、最可靠的方式判断管理员
        if user.is_superuser:
            context.update(self.get_admin_dashboard_data())
        elif hasattr(user, 'role') and user.role == CustomUser.Role.TEACHER:
            context.update(self.get_teacher_dashboard_data())
        elif hasattr(user, 'role') and user.role == CustomUser.Role.STUDENT:
            context.update(self.get_student_dashboard_data())
        
        return context

    def get_admin_dashboard_data(self):
        """为管理员准备仪表盘数据，并使用缓存"""
        cache_key = 'admin_dashboard_data'
        cached_data = cache.get(cache_key)

        if cached_data:
            print("DEBUG: 管理员数据从缓存加载...") # 方便您在终端看到效果
            return cached_data

        print("DEBUG: 缓存未命中，正在为管理员查询数据库...")
        
        # 1. 院系学生人数分布
        dept_student_counts = (
            Department.objects.annotate(student_count=Count('student'))
            .filter(student_count__gt=0).values('dept_name', 'student_count')
        )
        
        # 2. 全校成绩分布
        grade_distribution = Grade.objects.aggregate(
            excellent=Count("pk", filter=Q(score__gte=90)),
            good=Count("pk", filter=Q(score__gte=80, score__lt=90)),
            satisfactory=Count("pk", filter=Q(score__gte=70, score__lt=80)),
            pass_grade=Count("pk", filter=Q(score__gte=60, score__lt=70)),
            fail=Count("pk", filter=Q(score__lt=60)),
        )

        data = {
            "page_title": "系统仪表盘 (管理员)",
            "show_dashboard": True,
            # 图表一数据
            "chart_1_title": json.dumps("院系学生人数分布"),
            "chart_1_labels": json.dumps([item["dept_name"] for item in dept_student_counts]),
            "chart_1_data": json.dumps([item["student_count"] for item in dept_student_counts]),
            # 图表二数据
            "chart_2_title": json.dumps("全校成绩等级分布"),
            "chart_2_labels": json.dumps(["优秀", "良好", "中等", "及格", "不及格"]),
            "chart_2_data": json.dumps(list(grade_distribution.values())),
        }

        cache.set(cache_key, data, 600)  # 将数据缓存10分钟
        return data

    def get_teacher_dashboard_data(self):
        """为教师准备仪表盘数据，并使用缓存"""
        teacher_id = self.request.user.pk
        cache_key = f'teacher_dashboard_data_{teacher_id}'
        cached_data = cache.get(cache_key)

        if cached_data:
            print(f"DEBUG: 教师 {teacher_id} 的数据从缓存加载...")
            return cached_data

        print(f"DEBUG: 缓存未命中，正在为教师 {teacher_id} 查询数据库...")
        
        try:
            teacher = self.request.user.teacher_profile
        except Teacher.DoesNotExist:
             return {"show_dashboard": False, "page_title": "教师仪表盘"}

        # 1. 教师所授课程的学生人数
        assignments = TeachingAssignment.objects.filter(teacher=teacher).annotate(
            enrollment_count=Count('courseenrollment')
        ).filter(enrollment_count__gt=0)
        
        course_labels = [f"{assign.course.course_name} ({assign.semester})" for assign in assignments]
        course_data = [assign.enrollment_count for assign in assignments]

        data = {
            "page_title": f"教师仪表盘 ({teacher.name})",
            "show_dashboard": True,
            # 图表一数据
            "chart_1_title": json.dumps("我教授的课程学生人数"),
            "chart_1_labels": json.dumps(course_labels),
            "chart_1_data": json.dumps(course_data),
            # 教师视图不展示第二个图表
            "chart_2_labels": json.dumps([]),
            "chart_2_data": json.dumps([]),
        }

        cache.set(cache_key, data, 600) # 缓存10分钟
        return data
    
    def get_student_dashboard_data(self):
        """为学生准备仪表盘数据"""
        return {
             "page_title": "学生个人主页",
             "show_dashboard": False, # 学生的仪表盘不显示图表
        }

