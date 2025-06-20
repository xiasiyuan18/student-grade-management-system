# users/frontend_views.py
import pandas as pd
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q

# 确保导入了所有我们需要的、正确的表单
from .forms import (
    TeacherCreateForm, TeacherUpdateForm, StudentCreateForm, StudentProfileUpdateForm, 
    TeacherProfileUpdateForm, StudentUpdateForm, StudentProfileEditForm
)
from .models import Teacher, Student 
from common.mixins import (
    AdminRequiredMixin, StudentRequiredMixin, 
    TeacherRequiredMixin, SensitiveInfoMixin
)

User = get_user_model()


# =============================================================================
# 管理员功能 - 学生管理
# =============================================================================
class StudentListView(AdminRequiredMixin, SensitiveInfoMixin, generic.ListView):
    model = Student
    template_name = 'users/student_list.html'
    context_object_name = 'students'
    paginate_by = 15  # 每页显示15条记录

    def get_queryset(self):
        """
        重写此方法以支持搜索功能。
        """
        # ✅ 确保我们从完整的学生列表开始
        # 使用 select_related 优化数据库查询，一次性获取关联对象
        queryset = Student.objects.select_related(
            'user', 'department', 'major', 'minor_major'
        ).order_by('student_id_num')

        # 获取 GET 请求中的搜索参数 'q'
        search_query = self.request.GET.get('q', None)
        
        if search_query:
            # 如果有搜索词，则进行多字段模糊查询
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(student_id_num__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(major__major_name__icontains=search_query) |
                Q(department__dept_name__icontains=search_query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        """
        将搜索词传递到模板，以便在搜索框中显示。
        """
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context

class StudentCreateView(AdminRequiredMixin, SuccessMessageMixin, generic.FormView):
    form_class = StudentCreateForm
    template_name = 'users/student_form.html'
    success_url = reverse_lazy('users:student-list')
    success_message = "新学生 '%(name)s' (用户名: %(username)s) 已成功创建！"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    # ✨ 关键：修正 get_success_message 方法
    def get_success_message(self, cleaned_data):
        # 直接使用传入的 cleaned_data 字典，而不是 self.get_form()
        return self.success_message % {
            'name': cleaned_data.get('name'),
            'username': cleaned_data.get('username')
        }
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '添加新学生'
        return context
class StudentUpdateView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = User 
    form_class = StudentUpdateForm
    template_name = 'users/user_form_simple.html'
    success_url = reverse_lazy('users:student-list')
    success_message = "学生账户信息已成功更新！"
    
    def get_queryset(self):
        return User.objects.filter(role=User.Role.STUDENT)

class StudentProfileEditView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = Student
    form_class = StudentProfileEditForm
    template_name = 'users/student_profile_edit.html'
    success_url = reverse_lazy('users:student-list')
    success_message = "学生档案信息已成功更新！"

class StudentDeleteView(AdminRequiredMixin, generic.DeleteView):
    model = User
    template_name = 'users/student_confirm_delete.html'
    success_url = reverse_lazy('users:student-list')

    def form_valid(self, form):
        messages.success(self.request, f"学生 {self.object.username} 已成功删除。")
        return super().form_valid(form)

    def get_queryset(self):
        return User.objects.filter(role=User.Role.STUDENT)


# =============================================================================
# 管理员功能 - 教师管理
# =============================================================================
class TeacherListView(AdminRequiredMixin, SensitiveInfoMixin, generic.ListView):
    model = Teacher
    template_name = 'users/teacher_list.html'
    context_object_name = 'teachers'
    paginate_by = 15

    def get_queryset(self):
        queryset = Teacher.objects.select_related('user', 'department').order_by('-user__date_joined')
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(teacher_id_num__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(department__dept_name__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context

class TeacherCreateView(AdminRequiredMixin, SuccessMessageMixin, generic.FormView):
    form_class = TeacherCreateForm
    template_name = 'users/teacher_form.html'
    success_url = reverse_lazy('users:teacher-list')
    success_message = "新教师 '%(name)s' (用户名: %(username)s) 已成功创建！"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    # ✨ 关键：修正 get_success_message 方法
    def get_success_message(self, cleaned_data):
        # 直接使用传入的 cleaned_data 字典
        return self.success_message % {
            'name': cleaned_data.get('name'),
            'username': cleaned_data.get('username')
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '新增教师'
        return context


class TeacherUpdateView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = Teacher
    form_class = TeacherUpdateForm
    template_name = 'users/teacher_form.html'
    success_url = reverse_lazy('users:teacher-list')
    success_message = "教师信息已成功更新！"
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '编辑教师信息'
        return context

class TeacherDeleteView(AdminRequiredMixin, generic.DeleteView):
    model = User
    template_name = 'users/teacher_confirm_delete.html'
    success_url = reverse_lazy('users:teacher-list')
    
    def get_queryset(self):
        return User.objects.filter(role=User.Role.TEACHER)
    
    def form_valid(self, form):
        messages.success(self.request, f"教师 {self.object.username} 已成功删除。")
        return super().form_valid(form)


# =============================================================================
# 学生与教师个人中心
# =============================================================================
class StudentProfileUpdateView(StudentRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = Student
    form_class = StudentProfileUpdateForm
    template_name = 'users/student_profile_update.html'
    success_url = reverse_lazy('common:student-info')
    success_message = "您的个人信息已成功更新！"

    def get_object(self, queryset=None):
        return get_object_or_404(Student, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '修改个人信息'
        return context

class TeacherProfileUpdateView(TeacherRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = User
    form_class = TeacherProfileUpdateForm
    template_name = 'users/user_profile_form.html'
    success_url = reverse_lazy('home')
    success_message = "您的个人信息已成功更新！"

    def get_object(self, queryset=None):
        return self.request.user

class StudentExportExcelView(AdminRequiredMixin, generic.View):
    def get(self, request, *args, **kwargs):
        # 获取所有学生数据
        students = Student.objects.select_related('user', 'major', 'department').all()
        
        # 准备数据
        data = {
            '学号': [s.student_id_num for s in students],
            '姓名': [s.name for s in students],
            '登录用户名': [s.user.username for s in students],
            '性别': [s.gender for s in students],
            '院系': [s.department.dept_name for s in students],
            '专业': [s.major.major_name for s in students],
            '入学年份': [s.grade_year for s in students],
            '联系电话': [s.phone for s in students],
        }
        
        df = pd.DataFrame(data)
        
        # 创建一个 HTTP 响应，内容类型为 Excel
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        # 设置文件名
        response['Content-Disposition'] = 'attachment; filename="students_export.xlsx"'
        
        # 将 DataFrame 写入响应
        df.to_excel(response, index=False, engine='openpyxl')
        
        return response
