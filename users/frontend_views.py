from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import get_user_model

from .models import Teacher, Student 
# ✨ 关键修正：从 .forms 文件中导入所有需要的表单类
from .forms import TeacherForm, StudentForm, StudentProfileUpdateForm

User = get_user_model()

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

# =============================================================================
# 教师管理视图 (管理员视角)
# =============================================================================
class TeacherListView(AdminRequiredMixin, generic.ListView):
    model = Teacher
    template_name = 'users/teacher_list.html'
    context_object_name = 'teachers'
    queryset = Teacher.objects.select_related('user').order_by('-user__date_joined')

class TeacherCreateView(AdminRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = User
    form_class = TeacherForm
    template_name = 'users/teacher_form.html'
    success_url = reverse_lazy('users:teacher-list')
    success_message = "教师 %(username)s 已成功创建！"

    def get_success_message(self, cleaned_data):
        return self.success_message % {'username': self.object.username}

class TeacherUpdateView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = User
    form_class = TeacherForm
    template_name = 'users/teacher_form.html'
    success_url = reverse_lazy('users:teacher-list')
    success_message = "教师 %(username)s 的信息已成功更新！"

    def get_success_message(self, cleaned_data):
        return self.success_message % {'username': self.object.username}

class TeacherDeleteView(AdminRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    model = User
    template_name = 'users/teacher_confirm_delete.html'
    success_url = reverse_lazy('users:teacher-list')
    success_message = "教师已成功删除。"


# =============================================================================
# 学生管理视图 (管理员视角)
# =============================================================================
class StudentListView(AdminRequiredMixin, generic.ListView):
    model = Student
    template_name = 'users/student_list.html'
    context_object_name = 'students'
    queryset = Student.objects.select_related('user', 'major', 'department').order_by('-user__date_joined')

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
    # 这个视图可能需要进一步完善，但目前不会引起启动错误
    model = User 
    fields = ['username', 'email']
    template_name = 'users/user_form_simple.html'
    success_url = reverse_lazy('users:student-list')
    success_message = "学生账户信息已成功更新！"

class StudentProfileUpdateView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    # 这个视图也可能需要进一步完善，但目前不会引起启动错误
    model = Student
    form_class = StudentProfileUpdateForm
    template_name = 'users/student_profile_form.html'
    success_url = reverse_lazy('users:student-list')
    success_message = "学生档案已成功保存！"

    def get_object(self, queryset=None):
        user = get_object_or_404(User, pk=self.kwargs['pk'], role=User.Role.STUDENT)
        student_profile, created = Student.objects.get_or_create(user=user)
        return student_profile

class StudentDeleteView(AdminRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    model = User
    template_name = 'users/student_confirm_delete.html'
    success_url = reverse_lazy('users:student-list')
    success_message = "学生已成功删除。"