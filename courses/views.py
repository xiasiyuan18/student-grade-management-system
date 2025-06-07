# student_grade_management_system/courses/views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import HttpResponseRedirect # 导入这个
from django.shortcuts import get_object_or_404 # 如果你需要根据PK获取对象，或者在删除时使用

from .models import Course, TeachingAssignment
from .forms import CourseForm, TeachingAssignmentForm # 导入 Forms
from users.models import CustomUser # 导入 CustomUser 模型，用于检查角色

# 辅助函数：检查用户角色 (假设CustomUser模型有role字段)
def is_admin(user):
    # 确保 user.CustomUser.Role 存在，因为它是枚举
    return user.is_superuser or (hasattr(user, 'role') and user.role == CustomUser.Role.ADMIN)


# --- Course CRUD 视图 (用于渲染模板) ---

class CourseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses' # 在模板中使用 'courses' 变量来访问列表
    paginate_by = 10 # 每页显示10条记录 (可选)

    def test_func(self):
        # 只有管理员才能查看课程列表
        return is_admin(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "您没有权限访问课程管理页面。")
        return super().handle_no_permission()

class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('courses:course_list') # 成功后重定向到列表页

    def test_func(self):
        return is_admin(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"课程 '{form.instance.course_name}' 创建成功！")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "课程创建失败，请检查输入。")
        return super().form_invalid(form)

    def handle_no_permission(self):
        messages.error(self.request, "您没有权限创建课程。")
        return super().handle_no_permission()


class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('courses:course_list')

    def test_func(self):
        return is_admin(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"课程 '{form.instance.course_name}' 更新成功！")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "课程更新失败，请检查输入。")
        return super().form_invalid(form)

    def handle_no_permission(self):
        messages.error(self.request, "您没有权限编辑课程。")
        return super().handle_no_permission()


class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('courses:course_list')
    context_object_name = 'course' # 模板中使用的对象名

    def test_func(self):
        return is_admin(self.request.user)

    # Django DeleteView 默认通过 POST 请求删除，成功后重定向。
    # 这里重写 delete 方法是为了添加 messages。
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        course_name = self.object.course_name # 在删除前获取名称
        self.object.delete()
        messages.success(request, f"课程 '{course_name}' 删除成功！")
        return HttpResponseRedirect(self.get_success_url())

    def handle_no_permission(self):
        messages.error(self.request, "您没有权限删除课程。")
        return super().handle_no_permission()

# --- TeachingAssignment CRUD 视图 (如果需要模板渲染管理，可以类似添加) ---
# 目前文档主要聚焦课程管理和成绩录入，这里暂时不提供完整的 TeachingAssignment CRUD 视图
# 但如果需要，可以参考 Course CRUD 的模式进行扩展