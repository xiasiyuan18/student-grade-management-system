# departments/frontend_views.py
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin # 确保 UserPassesTestMixin 已导入
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Department, Major
from .forms import DepartmentForm, MajorForm # 确保这个 forms.py 文件和这些表单已创建

# --- 权限控制 Mixin (确保这个 Mixin 已按需调整并能正常工作) ---
class AdminPermissionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy('frontend:users_frontend:login') # 确保登录URL正确

    def test_func(self):
        user = self.request.user
        return user.is_superuser or \
               (hasattr(user, 'role') and user.role == 'ADMIN')


# --- Department (院系) Views ---
class DepartmentListView(AdminPermissionRequiredMixin, ListView):
    model = Department
    template_name = 'departments/department_list.html'
    context_object_name = 'departments'

class DepartmentCreateView(AdminPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    success_url = reverse_lazy('frontend:departments_frontend:department_list')
    success_message = "院系 '%(dept_name)s' 创建成功！"

class DepartmentUpdateView(AdminPermissionRequiredMixin, SuccessMessageMixin, UpdateView): # <--- 这是你需要确保存在的类
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    success_url = reverse_lazy('frontend:departments_frontend:department_list')
    success_message = "院系 '%(dept_name)s' 更新成功！"

class DepartmentDeleteView(AdminPermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Department
    template_name = 'departments/department_confirm_delete.html'
    success_url = reverse_lazy('frontend:departments_frontend:department_list')
    def get_success_message(self, cleaned_data):
        return f"院系 '{self.object.dept_name}' 已成功删除！"


# --- Major (专业) Views ---
class MajorListView(AdminPermissionRequiredMixin, ListView):
    model = Major
    template_name = 'departments/major_list.html'
    context_object_name = 'majors'

class MajorCreateView(AdminPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Major
    form_class = MajorForm
    template_name = 'departments/major_form.html'
    success_url = reverse_lazy('frontend:departments_frontend:major_list')
    success_message = "专业 '%(major_name)s' 创建成功！"

class MajorUpdateView(AdminPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Major
    form_class = MajorForm
    template_name = 'departments/major_form.html'
    success_url = reverse_lazy('frontend:departments_frontend:major_list')
    success_message = "专业 '%(major_name)s' 更新成功！"

class MajorDeleteView(AdminPermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Major
    template_name = 'departments/major_confirm_delete.html'
    success_url = reverse_lazy('frontend:departments_frontend:major_list')
    def get_success_message(self, cleaned_data):
        return f"专业 '{self.object.major_name}' 已成功删除！"
