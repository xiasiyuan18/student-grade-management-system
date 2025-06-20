# student_grade_management_system/grades/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from decimal import Decimal, InvalidOperation

from .models import Grade, TeachingAssignment
from courses.models import CourseEnrollment
from users.models import Student, Teacher, CustomUser
from .forms import GradeFormForAdmin 
from common.mixins import TeacherRequiredMixin, StudentRequiredMixin, AdminRequiredMixin, OwnDataOnlyMixin


class TeacherCoursesView(TeacherRequiredMixin, generic.ListView):
    """教师查看自己教授的课程列表"""
    model = TeachingAssignment
    template_name = 'grades/teacher_course_list.html'
    context_object_name = 'assignments'
    
    def get_queryset(self):
        # 只显示当前登录教师的授课安排
        try:
            teacher_profile = self.request.user.teacher_profile
            if teacher_profile:
                return TeachingAssignment.objects.filter(
                    teacher=teacher_profile
                ).select_related('course', 'teacher').order_by('-semester', 'course__course_name')
            else:
                return TeachingAssignment.objects.none()
        except AttributeError:
            return TeachingAssignment.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '我的授课课程'
        return context


class TeacherStudentListView(TeacherRequiredMixin, generic.DetailView):
    """教师查看特定课程的学生名单"""
    model = TeachingAssignment
    template_name = 'grades/teacher_student_list.html'
    context_object_name = 'assignment'
    pk_url_kwarg = 'assignment_id'

    def get_queryset(self):
        try:
            teacher_profile = self.request.user.teacher_profile
            if teacher_profile:
                return TeachingAssignment.objects.filter(teacher=teacher_profile)
            return TeachingAssignment.objects.none()
        except AttributeError:
            return TeachingAssignment.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.get_object()
        enrollments = CourseEnrollment.objects.filter(
            teaching_assignment=assignment,
            status='ENROLLED'
        ).select_related('student__user', 'student__major').order_by('student__student_id_num')
        
        context['enrollments'] = enrollments
        context['page_title'] = f'"{assignment.course.course_name}" 学生名单'
        return context


class GradeEntryView(TeacherRequiredMixin, View):
    """教师录入成绩"""
    template_name = 'grades/grade_entry_form.html'
    
    def get(self, request, assignment_id):
        assignment = get_object_or_404(TeachingAssignment, pk=assignment_id)
        
        try:
            if assignment.teacher != request.user.teacher_profile:
                messages.error(request, "您只能录入自己教授课程的成绩")
                return redirect('grades:teacher-courses')
        except AttributeError:
            messages.error(request, "您没有教师权限")
            return redirect('home')
        
        enrollments = CourseEnrollment.objects.filter(
            teaching_assignment=assignment,
            status='ENROLLED'
        ).select_related('student__user', 'student__department').order_by('student__student_id_num')
        
        existing_grades = {
            grade.student.pk: grade for grade in Grade.objects.filter(teaching_assignment=assignment)
        }
        
        student_data = []
        for enrollment in enrollments:
            student = enrollment.student
            existing_grade = existing_grades.get(student.pk)
            student_data.append({
                'student': student,
                'enrollment': enrollment,
                'existing_grade': existing_grade,
            })
        
        context = {
            'assignment': assignment,
            'student_data': student_data,
            'page_title': f'成绩录入 - {assignment.course.course_name}',
        }
        
        return render(request, self.template_name, context)

    def post(self, request, assignment_id):
        assignment = get_object_or_404(TeachingAssignment, pk=assignment_id)
        
        try:
            if assignment.teacher != request.user.teacher_profile:
                messages.error(request, "权限错误")
                return redirect('grades:teacher-courses')
        except AttributeError:
            return redirect('home')
        
        updated_count = 0
        error_count = 0
        error_details = []
        
        for key, value in request.POST.items():
            if key.startswith('score_') and value.strip():
                try:
                    student_pk = int(key.replace('score_', ''))
                    score_val = Decimal(value)
                    
                    if not (0 <= score_val <= 100):
                        error_count += 1
                        error_details.append(f"学生ID {student_pk}: 分数 {score_val} 超出有效范围(0-100)")
                        continue
                    
                    try:
                        student = Student.objects.get(pk=student_pk)
                    except Student.DoesNotExist:
                        error_count += 1
                        error_details.append(f"学生ID {student_pk}: 学生不存在")
                        continue
                    
                    enrollment = CourseEnrollment.objects.filter(
                        student=student, 
                        teaching_assignment=assignment
                    ).first()
                    
                    if not enrollment:
                        error_count += 1
                        error_details.append(f"学生 {student.name}({student.student_id_num}): 未找到选课记录")
                        continue
                    
                    if enrollment.status != 'ENROLLED':
                        error_count += 1
                        error_details.append(f"学生 {student.name}({student.student_id_num}): 选课状态为 '{enrollment.status}'，不是 'ENROLLED'")
                        continue
                    
                    grade, created = Grade.objects.update_or_create(
                        student=student,
                        teaching_assignment=assignment,
                        defaults={'score': score_val, 'last_modified_by': request.user}
                    )
                    updated_count += 1
                    
                except (ValueError, InvalidOperation) as e:
                    error_count += 1
                    error_details.append(f"学生ID {student_pk}: 分数格式错误 - {str(e)}")
                    continue
                except Exception as e:
                    error_count += 1
                    error_details.append(f"学生ID {student_pk}: 未知错误 - {str(e)}")
                    continue
    
        if updated_count > 0:
            messages.success(request, f"成功录入/更新了 {updated_count} 条成绩记录。")
        
        if error_count > 0:
            messages.warning(request, f"有 {error_count} 条记录录入失败，详细信息：")
            for detail in error_details[:10]:
                messages.error(request, detail)
            if len(error_details) > 10:
                messages.error(request, f"还有 {len(error_details) - 10} 个错误未显示...")
    
        return redirect('grades:grade-entry', assignment_id=assignment_id)


class MyGradesView(StudentRequiredMixin, generic.ListView):
    """学生查看自己的成绩"""
    model = Grade
    template_name = 'grades/my_grades.html'
    context_object_name = 'grades_list'

    def get_queryset(self):
        try:
            student_profile = self.request.user.student_profile
            if student_profile:
                return Grade.objects.filter(
                    student=student_profile
                ).select_related(
                    'teaching_assignment__course',
                    'teaching_assignment__teacher'
                ).order_by('-teaching_assignment__semester', 'teaching_assignment__course__course_name')
            else:
                return Grade.objects.none()
        except AttributeError:
            return Grade.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '我的成绩'
        
        grades = context['grades_list']
        
        if grades.exists():
            total_courses = grades.count()
            graded_courses = grades.filter(score__isnull=False)
            completed_courses = graded_courses.filter(score__gte=60).count()
            
            # 计算总学分
            total_credits = sum(
                grade.teaching_assignment.course.credits 
                for grade in graded_courses.filter(score__gte=60)
                if grade.teaching_assignment and grade.teaching_assignment.course
            )
            
            # 计算平均分
            avg_score = graded_courses.aggregate(avg=Avg('score'))['avg']
            if avg_score:
                avg_score = round(float(avg_score), 2)
            
            # 计算加权平均分
            weighted_total = 0
            credit_total = 0
            for grade in graded_courses:
                if grade.score is not None and grade.teaching_assignment and grade.teaching_assignment.course:
                    credits = grade.teaching_assignment.course.credits
                    weighted_total += float(grade.score) * float(credits)
                    credit_total += float(credits)
            
            weighted_avg_score = round(weighted_total / credit_total, 2) if credit_total > 0 else None
            
            # 成绩分布
            grade_distribution = {
                'excellent': graded_courses.filter(score__gte=90).count(),
                'good': graded_courses.filter(score__gte=80, score__lt=90).count(),
                'average': graded_courses.filter(score__gte=70, score__lt=80).count(),
                'pass': graded_courses.filter(score__gte=60, score__lt=70).count(),
                'fail': graded_courses.filter(score__lt=60).count(),
            }
            
            # GPA统计
            gpa_grades = graded_courses.exclude(gpa__isnull=True)
            if gpa_grades.exists():
                avg_gpa = gpa_grades.aggregate(avg=Avg('gpa'))['avg']
                if avg_gpa:
                    avg_gpa = round(float(avg_gpa), 2)
                
                # 按学分加权的GPA
                weighted_gpa_total = 0
                gpa_credit_total = 0
                for grade in gpa_grades:
                    if grade.gpa is not None and grade.teaching_assignment and grade.teaching_assignment.course:
                        credits = grade.teaching_assignment.course.credits
                        weighted_gpa_total += float(grade.gpa) * float(credits)
                        gpa_credit_total += float(credits)
                
                weighted_avg_gpa = round(weighted_gpa_total / gpa_credit_total, 2) if gpa_credit_total > 0 else None
            else:
                avg_gpa = None
                weighted_avg_gpa = None
            
            # 通过率
            pass_rate = round(completed_courses / total_courses * 100, 1) if total_courses > 0 else 0
            
            context.update({
                'total_courses': total_courses,
                'completed_courses': completed_courses,
                'graded_courses': graded_courses.count(),
                'ungraded_courses': total_courses - graded_courses.count(),
                'total_credits': total_credits,
                'average_score': avg_score,
                'weighted_average_score': weighted_avg_score,
                'avg_gpa': avg_gpa,
                'weighted_avg_gpa': weighted_avg_gpa,
                'pass_rate': pass_rate,
                'grade_distribution': grade_distribution,
            })
            
            # 按学期分组
            semester_grades = {}
            for grade in grades:
                semester = grade.teaching_assignment.semester
                if semester not in semester_grades:
                    semester_grades[semester] = []
                semester_grades[semester].append(grade)
            
            context['semester_grades'] = semester_grades
            
        else:
            context.update({
                'total_courses': 0, 'completed_courses': 0, 'graded_courses': 0,
                'ungraded_courses': 0, 'total_credits': 0, 'average_score': None,
                'weighted_average_score': None, 'avg_gpa': None, 'weighted_avg_gpa': None,
                'pass_rate': 0,
                'grade_distribution': {'excellent': 0, 'good': 0, 'average': 0, 'pass': 0, 'fail': 0,},
                'semester_grades': {},
            })
        
        return context


class GradeDeleteView(TeacherRequiredMixin, View):
    """教师删除成绩记录"""
    
    def post(self, request, grade_id):
        grade = get_object_or_404(Grade, pk=grade_id)
        
        try:
            teacher_profile = request.user.teacher_profile
            if grade.teaching_assignment.teacher != teacher_profile:
                messages.error(request, "您只能删除自己教授课程的成绩")
                return redirect('grades:teacher-courses')
        except AttributeError:
            messages.error(request, "您没有教师权限")
            return redirect('home')
        
        assignment_id = grade.teaching_assignment.id
        student_name = grade.student.name
        course_name = grade.teaching_assignment.course.course_name
        
        grade.delete()
        
        messages.success(request, f"已删除学生 {student_name} 在课程 {course_name} 中的成绩记录")
        return redirect('grades:grade-entry', assignment_id=assignment_id)


class AdminGradeListView(AdminRequiredMixin, generic.ListView):
    """管理员查看和筛选所有成绩"""
    model = Grade
    template_name = 'grades/admin_grade_list.html'
    context_object_name = 'grades'
    paginate_by = 20

    def get_queryset(self):
        queryset = Grade.objects.select_related(
            'student__user', 
            'teaching_assignment__course', 
            'teaching_assignment__teacher'
        ).order_by('-entry_time')

        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(student__name__icontains=search_query) |
                Q(student__student_id_num__icontains=search_query) |
                Q(teaching_assignment__course__course_name__icontains=search_query) |
                Q(teaching_assignment__course__course_id__icontains=search_query) |
                Q(teaching_assignment__teacher__name__icontains=search_query) |
                Q(teaching_assignment__semester__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '全局成绩管理'
        context['search_query'] = self.request.GET.get('q', '')
        return context


class AdminGradeUpdateView(AdminRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    """管理员修改成绩"""
    model = Grade
    form_class = GradeFormForAdmin
    template_name = 'grades/admin_grade_form.html'
    success_url = reverse_lazy('grades:admin-grade-list')
    success_message = "成绩记录已成功更新。"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '修改成绩'
        return context

    def form_valid(self, form):
        form.instance.last_modified_by = self.request.user
        return super().form_valid(form)


class AdminGradeDeleteView(AdminRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """管理员删除成绩"""
    model = Grade
    template_name = 'grades/admin_grade_confirm_delete.html'
    success_url = reverse_lazy('grades:admin-grade-list')
    success_message = "成绩记录已成功删除。"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '确认删除成绩'
        return context