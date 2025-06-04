from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# 从当前应用的 models.py 中导入模型 (使用正确的模型名称)
from .models import Teacher, Student

# ---- 通用权限控制 ----
# 只有管理员才能访问的视图
class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

# ---- 教师管理视图 (管理员视角) ----

class TeacherListView(AdminRequiredMixin, generic.ListView):
    model = Teacher  # 修正: TeacherProfile -> Teacher
    template_name = 'users/teacher_list.html'
    context_object_name = 'teachers'

class TeacherCreateView(AdminRequiredMixin, generic.CreateView):
    model = Teacher  # 修正: TeacherProfile -> Teacher
    template_name = 'users/teacher_form.html'
    fields = ['user', 'teacher_id_num', 'name', 'department'] # 根据 Teacher 模型字段调整
    success_url = reverse_lazy('frontend:users_frontend:teacher_list')

class TeacherUpdateView(AdminRequiredMixin, generic.UpdateView):
    model = Teacher  # 修正: TeacherProfile -> Teacher
    template_name = 'users/teacher_form.html'
    fields = ['teacher_id_num', 'name', 'department'] # user 是主键，通常在更新时不可编辑
    success_url = reverse_lazy('frontend:users_frontend:teacher_list')

class TeacherDeleteView(AdminRequiredMixin, generic.DeleteView):
    model = Teacher  # 修正: TeacherProfile -> Teacher
    template_name = 'users/teacher_confirm_delete.html'
    success_url = reverse_lazy('frontend:users_frontend:teacher_list')


# ---- 学生管理视图 (管理员视角) ----

class StudentListView(AdminRequiredMixin, generic.ListView):
    model = Student  # 修正: StudentProfile -> Student
    template_name = 'users/student_list.html'
    context_object_name = 'students'

class StudentCreateView(AdminRequiredMixin, generic.CreateView):
    model = Student  # 修正: StudentProfile -> Student
    template_name = 'users/student_form.html'
    fields = ['user', 'student_id_num', 'name', 'id_card', 'gender', 'birth_date', 'phone', 'dormitory', 'home_address', 'grade_year', 'major', 'department', 'degree_level'] # 根据 Student 模型字段调整
    success_url = reverse_lazy('frontend:users_frontend:student_list')

class StudentUpdateView(AdminRequiredMixin, generic.UpdateView):
    model = Student  # 修正: StudentProfile -> Student
    template_name = 'users/student_form.html'
    fields = ['student_id_num', 'name', 'id_card', 'gender', 'birth_date', 'phone', 'dormitory', 'home_address', 'grade_year', 'major', 'department', 'degree_level']
    success_url = reverse_lazy('frontend:users_frontend:student_list')

class StudentDeleteView(AdminRequiredMixin, generic.DeleteView):
    model = Student  # 修正: StudentProfile -> Student
    template_name = 'users/student_confirm_delete.html'
    success_url = reverse_lazy('frontend:users_frontend:student_list')


# ---- 个人信息修改视图 ----

class TeacherProfileSelfUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Teacher  # 修正: TeacherProfile -> Teacher
    template_name = 'users/profile_form.html'
    fields = ['name'] # 假设教师只能修改部分信息，可根据需求调整
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        return Teacher.objects.get(user=self.request.user)

class StudentProfileSelfUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Student  # 修正: StudentProfile -> Student
    template_name = 'users/profile_form.html'
    fields = ['phone', 'dormitory', 'home_address'] # 假设学生只能修改部分信息
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        return Student.objects.get(user=self.request.user)