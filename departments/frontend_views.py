# departments/frontend_views.py (添加回缺失的视图)

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin

from .models import Department, Major
from .forms import DepartmentForm, MajorForm
from common.mixins import AdminRequiredMixin


# --- 院系管理视图 (管理员) ---

class DepartmentListView(AdminRequiredMixin, generic.ListView):
    """院系列表"""
    model = Department
    template_name = 'departments/department_list.html'
    context_object_name = 'departments'
    paginate_by = 20

    def get_queryset(self):
        return Department.objects.all().order_by('dept_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 调试信息 - 查看Department模型字段
        departments = context['departments']
        print("=== Department调试信息 ===")
        print(f"Department模型主键字段: {Department._meta.pk.name}")
        
        # 获取Department模型的所有字段
        field_names = [f.name for f in Department._meta.get_fields()]
        print(f"Department模型字段: {field_names}")
        
        for dept in departments:
            print(f"Department: {dept.dept_name}")
            print(f"  - pk: '{dept.pk}' (type: {type(dept.pk)})")
            print(f"  - pk field name: {dept._meta.pk.name}")
            print("---")
        
        return context


class DepartmentCreateView(AdminRequiredMixin, SuccessMessageMixin, generic.CreateView):
    """创建院系"""
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    success_url = reverse_lazy('departments:department-list')
    success_message = "院系 '%(dept_name)s' 已成功创建！"


class DepartmentUpdateView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    """编辑院系"""
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    success_url = reverse_lazy('departments:department-list')
    success_message = "院系 '%(dept_name)s' 已成功更新！"


class DepartmentDeleteView(AdminRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """删除院系"""
    model = Department
    template_name = 'departments/department_confirm_delete.html'
    success_url = reverse_lazy('departments:department-list')
    success_message = "院系已成功删除！"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 检查是否有相关数据
        context['has_majors'] = Major.objects.filter(department=self.object).exists()
        return context


# --- 专业管理视图 (管理员) ---

class MajorListView(AdminRequiredMixin, generic.ListView):
    """专业列表"""
    model = Major
    template_name = 'departments/major_list.html'
    context_object_name = 'majors'
    paginate_by = 20

    def get_queryset(self):
        return Major.objects.select_related('department').order_by('department__dept_name', 'major_name')


class MajorCreateView(AdminRequiredMixin, SuccessMessageMixin, generic.CreateView):
    """创建专业"""
    model = Major
    form_class = MajorForm
    template_name = 'departments/major_form.html'
    success_url = reverse_lazy('departments:major-list')
    success_message = "专业 '%(major_name)s' 已成功创建！"


class MajorUpdateView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    """编辑专业"""
    model = Major
    form_class = MajorForm
    template_name = 'departments/major_form.html'
    success_url = reverse_lazy('departments:major-list')
    success_message = "专业 '%(major_name)s' 已成功更新！"


class MajorDeleteView(AdminRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """删除专业"""
    model = Major
    template_name = 'departments/major_confirm_delete.html'
    success_url = reverse_lazy('departments:major-list')
    success_message = "专业已成功删除！"