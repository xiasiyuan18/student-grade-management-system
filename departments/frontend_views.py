# departments/frontend_views.py (添加回缺失的视图)

from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Department, Major
from .forms import DepartmentForm, MajorForm

# --- 权限控制 Mixin ---
class AdminPermissionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    # 根据您之前的决定，我们指向 'login-page'
    login_url = reverse_lazy('users:login-page') 

    def test_func(self):
        user = self.request.user
        return user.is_superuser or \
               (hasattr(user, 'role') and user.role == 'ADMIN')


# --- Department (院系) Views ---

# ✨ 关键修正 #1：将缺失的 DepartmentListView 类加回来 ✨
class DepartmentListView(AdminPermissionRequiredMixin, ListView):
    model = Department
    template_name = 'departments/department_list.html'
    context_object_name = 'departments'


class DepartmentCreateView(AdminPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    # 根据您的决定，我们统一使用连字符 '-'
    success_url = reverse_lazy('departments:department-list')
    success_message = "院系 '%(dept_name)s' 创建成功！"

class DepartmentUpdateView(AdminPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    success_url = reverse_lazy('departments:department-list')
    success_message = "院系 '%(dept_name)s' 更新成功！"

class DepartmentDeleteView(AdminPermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Department
    template_name = 'departments/department_confirm_delete.html'
    success_url = reverse_lazy('departments:department-list')
    def get_success_message(self, cleaned_data):
        return f"院系 '{self.object.dept_name}' 已成功删除！"


# --- Major (专业) Views ---

# ✨ 关键修正 #2：将缺失的 MajorListView 类加回来 ✨
class MajorListView(AdminPermissionRequiredMixin, ListView):
    model = Major
    template_name = 'departments/major_list.html'
    context_object_name = 'majors'
    def get_queryset(self):
        """
        使用 select_related('department') 来优化查询，
        在查询 Major 的同时，通过数据库的 JOIN 操作一次性获取关联的 Department 对象。
        """
        queryset = super().get_queryset().select_related('department')
        return queryset


class MajorCreateView(AdminPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Major
    form_class = MajorForm
    template_name = 'departments/major_form.html'
    success_url = reverse_lazy('departments:major-list')
    success_message = "专业 '%(major_name)s' 创建成功！"

class MajorUpdateView(AdminPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Major
    form_class = MajorForm
    template_name = 'departments/major_form.html'
    success_url = reverse_lazy('departments:major-list')
    success_message = "专业 '%(major_name)s' 更新成功！"

class MajorDeleteView(AdminPermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Major
    template_name = 'departments/major_confirm_delete.html'
    success_url = reverse_lazy('departments:major-list')
    def get_success_message(self, cleaned_data):
        return f"专业 '{self.object.major_name}' 已成功删除！"