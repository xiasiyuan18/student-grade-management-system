from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import get_user_model
from .forms import TeacherForm, StudentForm, StudentProfileUpdateForm, TeacherProfileUpdateForm 
from .models import Teacher, Student 
# ✨ 关键修正：从 .forms 文件中导入所有需要的表单类

User = get_user_model()

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

# =============================================================================
# 教师管理视图 (管理员视角)
# =============================================================================
class TeacherListView(AdminRequiredMixin, generic.ListView):
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
    # 这里依然是创建 User
    model = User
    form_class = TeacherForm
    template_name = 'users/teacher_form.html'
    success_url = reverse_lazy('users:teacher-list')
    success_message = "教师 %(username)s 已成功创建！"

    def form_valid(self, form):
        """
        在表单验证成功后，我们不仅要设置角色，
        还要为这个新用户创建一个关联的 Teacher 档案。
        """
        # 首先，像之前一样，设置角色并保存 User 对象
        user = form.save(commit=False) # 先不提交到数据库
        user.role = User.Role.TEACHER
        user.save() # 现在保存 User

        # ✨ 核心修正 2：为新创建的 User 创建一个 Teacher 档案
        # 这确保了数据的一致性
        Teacher.objects.create(user=user)

        # 将保存的 user 对象赋给 self.object，以便 success_message 能获取到
        self.object = user
        return super().form_valid(form)

    # get_success_message 方法现在可以正常工作了
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

# =============================================================================
# 学生个人中心 (学生视角)
# =============================================================================
class StudentProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, generic.UpdateView):
    # ✨ 注意：模型是 Student
    model = Student
    form_class = StudentProfileUpdateForm
    template_name = 'users/student_profile_form.html' # ✨ 使用一个学生专用的模板
    success_url = reverse_lazy('home')
    success_message = "你的个人档案已成功更新！"

    def get_object(self, queryset=None):
        """
        这个方法会返回当前登录用户所关联的那个 Student 档案对象。
        """
        # 尝试获取当前登录用户的学生档案，如果不存在则会返回404错误
        return get_object_or_404(Student, user=self.request.user)

    def test_func(self):
        """
        确保只有角色为'STUDENT'的用户才能访问。
        """
        return self.request.user.role == User.Role.STUDENT

class StudentDeleteView(AdminRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    model = User
    template_name = 'users/student_confirm_delete.html'
    success_url = reverse_lazy('users:student-list')
    success_message = "学生已成功删除。"

# =============================================================================
# 教师个人中心 (教师视角)
# =============================================================================
class TeacherProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, generic.UpdateView):
    # 我们要更新的是 User 模型
    model = User
    # 使用我们专门创建的个人信息表单
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