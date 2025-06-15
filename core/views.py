# core/views.py

import json
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Case, When, IntegerField
from django.core.cache import cache # ✨ 1. 导入缓存模块

# 导入所有需要的模型
from departments.models import Department
from users.models import Student, CustomUser
from courses.models import Course, TeachingAssignment
from grades.models import Grade

class HomeView(LoginRequiredMixin, generic.TemplateView):
    """
    系统主页视图，应用了缓存来提升仪表盘加载速度。
    """
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['page_title'] = '欢迎使用学生成绩管理系统'
        
        if user.role in [CustomUser.Role.ADMIN, CustomUser.Role.TEACHER]:
            context['show_dashboard'] = True

            # ✨ 2. 尝试从缓存中获取数据
            dashboard_data = cache.get('dashboard_data')

            # 如果缓存中没有数据 (cache miss)
            if not dashboard_data:
                print("DEBUG: 缓存未命中，正在从数据库查询...") # 方便您在终端看到效果
                dashboard_data = {}

                # --- 执行昂贵的数据库查询 ---
                dashboard_data['department_count'] = Department.objects.count()
                dashboard_data['student_count'] = Student.objects.count()
                dashboard_data['teacher_count'] = CustomUser.objects.filter(role=CustomUser.Role.TEACHER).count()
                dashboard_data['course_count'] = Course.objects.count()

                dept_student_counts = Student.objects.values('department__dept_name').annotate(count=Count('user')).order_by('-count')
                dashboard_data['dept_chart_labels'] = [item['department__dept_name'] for item in dept_student_counts]
                dashboard_data['dept_chart_data'] = [item['count'] for item in dept_student_counts]

                gender_counts = Student.objects.values('gender').annotate(count=Count('gender')).order_by('gender')
                dashboard_data['gender_chart_labels'] = [item['gender'] for item in gender_counts]
                dashboard_data['gender_chart_data'] = [item['count'] for item in gender_counts]
                
                most_enrolled_assignment = TeachingAssignment.objects.annotate(num_students=Count('enrolled_students')).order_by('-num_students').first()
                if most_enrolled_assignment:
                    grades = Grade.objects.filter(teaching_assignment=most_enrolled_assignment, score__isnull=False)
                    grade_dist_data = grades.aggregate(
                        A_level=Count(Case(When(score__gte=90, then=1), output_field=IntegerField())),
                        B_level=Count(Case(When(score__gte=80, score__lt=90, then=1), output_field=IntegerField())),
                        C_level=Count(Case(When(score__gte=70, score__lt=80, then=1), output_field=IntegerField())),
                        D_level=Count(Case(When(score__gte=60, score__lt=70, then=1), output_field=IntegerField())),
                        F_level=Count(Case(When(score__lt=60, then=1), output_field=IntegerField())),
                    )
                    dashboard_data['grade_chart_title'] = f"热门课程 '{most_enrolled_assignment.course.course_name}' 成绩分布"
                    dashboard_data['grade_chart_labels'] = ['优秀 (90-100)', '良好 (80-89)', '中等 (70-79)', '及格 (60-69)', '不及格 (<60)']
                    dashboard_data['grade_chart_data'] = list(grade_dist_data.values())
                
                # ✨ 3. 将查询结果存入缓存，设置超时时间为 600 秒 (10分钟)
                cache.set('dashboard_data', dashboard_data, 600)
            else:
                 print("DEBUG: 缓存命中！正在从缓存加载数据...")
            
            # ✨ 4. 将数据（无论是来自数据库还是缓存）添加到上下文中
            context.update(dashboard_data)
            
        else:
            context['show_dashboard'] = False
            
        return context
