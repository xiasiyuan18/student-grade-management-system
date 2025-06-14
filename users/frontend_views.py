from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import get_user_model
from .forms import TeacherForm, StudentForm, StudentProfileUpdateForm, TeacherProfileUpdateForm, StudentUpdateForm, StudentProfileEditForm
from .models import Teacher, Student 
from common.mixins import (
    AdminRequiredMixin, StudentRequiredMixin, 
    TeacherRequiredMixin, SensitiveInfoMixin
)

User = get_user_model()

# 管理员功能
class StudentListView(AdminRequiredMixin, SensitiveInfoMixin, generic.ListView):
    """学生列表 - 仅限管理员"""
    model = Student
    template_name = 'users/student_list.html'
    context_object_name = 'students'
    queryset = Student.objects.select_related('user', 'major', 'department').order_by('-user__date_joined')

class TeacherListView(AdminRequiredMixin, SensitiveInfoMixin, generic.ListView):
    """教师列表 - 仅限管理员"""
    # ✨ 核心修正 1：查询 User 模型，而不是 Teacher 模型
    model = User
    template_name = 'users/teacher_list.html'
    context_object_name = 'teachers' # 模板中的变量名保持不变

    def get_queryset(self):
        """
        重写查询方法，只返回角色为 'TEACHER' 的用户。
        """
        # 使用 self.model (即 User) 来查询
        qs = super().get_queryset() 
        # 筛选出所有角色是 TEACHER 的用户，并按加入日期排序
        return qs.filter(role=User.Role.TEACHER).order_by('-date_joined')

class TeacherCreateView(AdminRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = User
    form_class = TeacherForm
    template_name = 'users/teacher_form.html'
    success_url = reverse_lazy('users:teacher-list')
    success_message = "教师 %(username)s 已成功创建！"

    def form_valid(self, form):
        """
        在表单验证成功后，创建用户和教师档案
        """
        try:
            from django.db import transaction
            with transaction.atomic():
                # 保存用户但不提交到数据库
                user = form.save(commit=False)
                user.role = User.Role.TEACHER
                user.save()
                print(f"DEBUG: 创建用户成功 - {user.username}")

                # 创建教师档案
                teacher_profile = Teacher.objects.create(
                    user=user,
                    teacher_id_num=form.cleaned_data['teacher_id_num'],
                    name=form.cleaned_data['name'],
                    department=form.cleaned_data['department']
                )
                print(f"DEBUG: 创建教师档案成功 - {teacher_profile.name}")

                self.object = user
                # 注意：这里不要调用 super().form_valid(form)，因为会再次保存表单
                return super(generic.CreateView, self).form_valid(form)
                
        except Exception as e:
            print(f"ERROR: 创建教师时发生错误 - {str(e)}")
            import traceback
            traceback.print_exc()
            form.add_error(None, f"创建教师失败: {str(e)}")
            return self.form_invalid(form)

    def get_success_message(self, cleaned_data):
        return self.success_message % {'username': self.object.username}
    
    # test_func 是多余的，因为 AdminRequiredMixin 已经包含了它
    # def test_func(self):
    #     return self.request.user.is_superuser

class TeacherUpdateView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = User
    form_class = TeacherForm # 更新时也使用这个表单
    template_name = 'users/teacher_form.html'
    success_url = reverse_lazy('users:teacher-list')
    success_message = "教师 %(username)s 的信息已成功更新！"

    def get_queryset(self):
        """确保只能更新角色为教师的用户"""
        return User.objects.filter(role=User.Role.TEACHER)

    def get_success_message(self, cleaned_data):
        return self.success_message % {'username': self.object.username}

class TeacherDeleteView(AdminRequiredMixin, generic.DeleteView):
    model = User
    template_name = 'users/teacher_confirm_delete.html'
    success_url = reverse_lazy('users:teacher-list')
    # SuccessMessageMixin 在 DeleteView 中需要特殊处理，为简化暂时移除
    # success_message = "教师已成功删除。"

    def get_queryset(self):
        """确保只能删除角色为教师的用户"""
        return User.objects.filter(role=User.Role.TEACHER)
    
# =============================================================================
# 学生管理视图 (管理员视角)
# =============================================================================
class StudentCreateView(AdminRequiredMixin, SuccessMessageMixin, generic.FormView):
    form_class = StudentForm # 现在可以正确找到 StudentForm
    template_name = 'users/student_form.html'
    success_url = reverse_lazy('users:student-list')
    success_message = "学生 %(username)s 已成功创建！"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return self.success_message % {'username': cleaned_data['username']}

class StudentUpdateView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    """管理员编辑学生用户账户信息"""
    model = User 
    form_class = StudentUpdateForm
    template_name = 'users/user_form_simple.html'
    success_url = reverse_lazy('users:student-list')
    success_message = "学生账户信息已成功更新！"
    
    def get_queryset(self):
        """确保只能更新角色为学生的用户"""
        return User.objects.filter(role=User.Role.STUDENT)

class StudentProfileEditView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    """管理员编辑学生档案详细信息"""
    model = Student
    form_class = StudentProfileEditForm
    template_name = 'users/student_profile_edit.html'
    success_url = reverse_lazy('users:student-list')
    success_message = "学生档案信息已成功更新！"

# =============================================================================
# 学生个人中心 (学生视角)
# =============================================================================
class StudentProfileUpdateView(StudentRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    """学生修改自己个人信息 - 仅限学生本人"""
    model = Student
    form_class = StudentProfileUpdateForm
    template_name = 'users/student_profile_update.html'
    success_url = reverse_lazy('common:student-info')
    success_message = "您的个人信息已成功更新！"

    def get_object(self, queryset=None):
        """
        返回当前登录用户所关联的学生档案对象。
        """
        return get_object_or_404(Student, user=self.request.user)

    def test_func(self):
        """
        确保只有角色为'STUDENT'的用户才能访问。
        """
        return (hasattr(self.request.user, 'role') and 
                self.request.user.role == User.Role.STUDENT)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '修改个人信息'
        return context

class StudentDeleteView(AdminRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    model = User
    template_name = 'users/student_confirm_delete.html'
    success_url = reverse_lazy('users:student-list')
    success_message = "学生已成功删除。"

# =============================================================================
# 教师个人中心 (教师视角)
# =============================================================================
class TeacherProfileUpdateView(TeacherRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    """教师修改自己个人信息 - 仅限教师本人"""
    model = User
    form_class = TeacherProfileUpdateForm
    template_name = 'users/user_profile_form.html'  # 我们将创建一个通用的个人信息模板
    success_url = reverse_lazy('home') # 成功后跳转回主页
    success_message = "您的个人信息已成功更新！"

    def get_object(self, queryset=None):
        """
        这个关键方法会直接返回当前登录的用户对象，
        确保教师只能修改自己的信息。
        """
        return self.request.user

    def test_func(self):
        """
        这个测试函数确保只有角色为'TEACHER'的用户才能访问此页面。
        """
        return self.request.user.role == User.Role.TEACHER