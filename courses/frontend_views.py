# courses/frontend_views.py (这个文件用于前端页面视图)

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Course
from .forms import CourseForm
from users.models import CustomUser

# 权限检查辅助函数
def is_admin(user):
    return user.is_superuser or (hasattr(user, 'role') and user.role == CustomUser.Role.ADMIN)

# --- Course CRUD 视图 (用于渲染模板) ---

class CourseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 10
    success_url = reverse_lazy('courses:course-list') # 修正：统一为连字符
    
    def test_func(self):
        return is_admin(self.request.user)
    # ... 其他方法 ...

class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('courses:course-list') # 修正：统一为连字符
    
    def test_func(self):
        return is_admin(self.request.user)
    def form_valid(self, form):
        messages.success(self.request, f"课程 '{form.instance.course_name}' 创建成功！")
        return super().form_valid(form)
    # ... 其他方法 ...

class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('courses:course-list') # 修正：统一为连字符

    def test_func(self):
        return is_admin(self.request.user)
    def form_valid(self, form):
        messages.success(self.request, f"课程 '{form.instance.course_name}' 更新成功！")
        return super().form_valid(form)
    # ... 其他方法 ...

class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('courses:course-list') # 修正：统一为连字符
    context_object_name = 'course'

    def test_func(self):
        return is_admin(self.request.user)
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        course_name = self.object.course_name
        self.object.delete()
        messages.success(request, f"课程 '{course_name}' 删除成功！")
        return HttpResponseRedirect(self.get_success_url())
    # ... 其他方法 ...