# core/views.py
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

# 导入需要的模型
from departments.models import Department, Major
from users.models import CustomUser
from courses.models import Course

class HomeView(LoginRequiredMixin, generic.TemplateView):
    """
    系统主页视图，现在集成了数据看板功能。
    """
    template_name = "core/home.html" # 确保模板路径正确

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 默认标题
        context['page_title'] = '欢迎使用学生成绩管理系统'
        
        # 只有管理员和教师能看到数据看板
        if user.role in [CustomUser.Role.ADMIN, CustomUser.Role.TEACHER]:
            context['show_dashboard'] = True
            context['department_count'] = Department.objects.count()
            context['major_count'] = Major.objects.count()
            context['student_count'] = CustomUser.objects.filter(role=CustomUser.Role.STUDENT).count()
            context['teacher_count'] = CustomUser.objects.filter(role=CustomUser.Role.TEACHER).count()
            context['course_count'] = Course.objects.count()
        else:
            context['show_dashboard'] = False
            
        return context
