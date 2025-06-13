# courses/frontend_views.py (这个文件用于前端页面视图)

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from .models import Course, TeachingAssignment, CourseEnrollment
from .forms import TeachingAssignmentForm
from users.models import Student

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires the user to be an admin (staff user).
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff
    
    def handle_no_permission(self):
        raise PermissionDenied("You must be an admin to access this page.")

# --- 课程管理视图 (管理员视角) ---

class CourseListView(AdminRequiredMixin, generic.ListView):
    """课程列表"""
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        return Course.objects.select_related('department').order_by('department__dept_name', 'course_name')

# --- 授课安排管理视图 (管理员视角) ---

class TeachingAssignmentListView(AdminRequiredMixin, generic.ListView):
    """授课安排列表"""
    model = TeachingAssignment
    template_name = 'courses/teaching_assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        # 根据实际存在的字段进行排序
        return TeachingAssignment.objects.select_related(
            'teacher__user', 'teacher__department', 'course__department'
        ).order_by('semester', 'course__course_name', 'teacher__name')

class TeachingAssignmentCreateView(AdminRequiredMixin, SuccessMessageMixin, generic.CreateView):
    """创建授课安排"""
    model = TeachingAssignment
    form_class = TeachingAssignmentForm
    template_name = 'courses/teaching_assignment_form.html'
    success_url = reverse_lazy('courses:teaching-assignment-list')
    success_message = "授课安排已成功创建！"

class TeachingAssignmentUpdateView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    """编辑授课安排"""
    model = TeachingAssignment
    form_class = TeachingAssignmentForm
    template_name = 'courses/teaching_assignment_form.html'
    success_url = reverse_lazy('courses:teaching-assignment-list')
    success_message = "授课安排已成功更新！"

class TeachingAssignmentDeleteView(AdminRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """删除授课安排"""
    model = TeachingAssignment
    template_name = 'courses/teaching_assignment_confirm_delete.html'
    success_url = reverse_lazy('courses:teaching-assignment-list')
    success_message = "授课安排已成功删除！"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 检查是否有相关的成绩记录
        from grades.models import Grade
        context['has_grades'] = Grade.objects.filter(teaching_assignment=self.object).exists()
        return context

# --- 选课记录管理视图 (管理员视角) ---

class CourseEnrollmentListView(AdminRequiredMixin, generic.ListView):
    """选课记录列表"""
    model = CourseEnrollment
    template_name = 'courses/course_enrollment_list.html'
    context_object_name = 'enrollments'
    paginate_by = 20

    def get_queryset(self):
        return CourseEnrollment.objects.select_related(
            'student__user', 'student__department',
            'teaching_assignment__course', 'teaching_assignment__teacher'
        ).order_by('-enrollment_date')

class CourseEnrollmentCreateView(AdminRequiredMixin, SuccessMessageMixin, generic.CreateView):
    """创建选课记录"""
    model = CourseEnrollment
    fields = ['student', 'teaching_assignment', 'status']
    template_name = 'courses/course_enrollment_form.html'
    success_url = reverse_lazy('courses:enrollment-list')
    success_message = "选课记录已成功创建！"

class CourseEnrollmentUpdateView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    """编辑选课记录"""
    model = CourseEnrollment
    fields = ['student', 'teaching_assignment', 'status']
    template_name = 'courses/course_enrollment_form.html'
    success_url = reverse_lazy('courses:enrollment-list')
    success_message = "选课记录已成功更新！"

class CourseEnrollmentDeleteView(AdminRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """删除选课记录"""
    model = CourseEnrollment
    template_name = 'courses/course_enrollment_confirm_delete.html'
    success_url = reverse_lazy('courses:enrollment-list')
    success_message = "选课记录已成功删除！"

class BulkEnrollmentView(AdminRequiredMixin, View):
    """批量选课"""
    template_name = 'courses/bulk_enrollment_form.html'
    
    def get(self, request):
        teaching_assignments = TeachingAssignment.objects.select_related('course', 'teacher').all()
        students = Student.objects.select_related('user', 'department').all()
        
        context = {
            'teaching_assignments': teaching_assignments,
            'students': students,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        assignment_id = request.POST.get('teaching_assignment')
        student_ids = request.POST.getlist('students')
        
        if not assignment_id or not student_ids:
            messages.error(request, "请选择授课安排和学生")
            return redirect('courses:bulk-enrollment')
        
        try:
            assignment = TeachingAssignment.objects.get(pk=assignment_id)
            enrolled_count = 0
            
            for student_id in student_ids:
                student = Student.objects.get(pk=student_id)
                enrollment, created = CourseEnrollment.objects.get_or_create(
                    student=student,
                    teaching_assignment=assignment,
                    defaults={'status': 'ENROLLED'}
                )
                if created:
                    enrolled_count += 1
            
            messages.success(request, f"成功为 {enrolled_count} 名学生完成选课")
            return redirect('courses:enrollment-list')
            
        except Exception as e:
            messages.error(request, f"选课操作失败: {str(e)}")
            return redirect('courses:bulk-enrollment')