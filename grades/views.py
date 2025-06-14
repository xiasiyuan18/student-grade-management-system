# student_grade_management_system/grades/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from decimal import Decimal

from .models import Grade, TeachingAssignment
from courses.models import CourseEnrollment
from users.models import Student, Teacher, CustomUser
from common.mixins import TeacherRequiredMixin, StudentRequiredMixin, OwnDataOnlyMixin


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


class GradeEntryView(TeacherRequiredMixin, View):
    """教师录入成绩"""
    template_name = 'grades/grade_entry_form.html'
    
    def get(self, request, assignment_id):
        """显示成绩录入页面"""
        # 验证教师只能访问自己的教学安排
        assignment = get_object_or_404(TeachingAssignment, pk=assignment_id)
        
        # 权限检查：确保是当前教师的课程
        try:
            teacher_profile = request.user.teacher_profile
            if assignment.teacher != teacher_profile:
                messages.error(request, "您只能录入自己教授课程的成绩")
                return redirect('grades:teacher-courses')
        except AttributeError:
            messages.error(request, "您没有教师权限")
            return redirect('home')
        
        # 获取选修此课程的学生列表
        enrollments = CourseEnrollment.objects.filter(
            teaching_assignment=assignment,
            status='ENROLLED'
        ).select_related('student__user', 'student__department').order_by('student__student_id_num')
        
        # 获取已有成绩记录
        existing_grades = {}
        grades = Grade.objects.filter(teaching_assignment=assignment)
        for grade in grades:
            existing_grades[grade.student.id] = grade
        
        # 为每个学生准备数据
        student_data = []
        for enrollment in enrollments:
            student = enrollment.student
            existing_grade = existing_grades.get(student.id)
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
        """处理成绩录入提交"""
        # 验证教师只能修改自己教授课程的成绩
        assignment = get_object_or_404(TeachingAssignment, pk=assignment_id)
        
        # 权限检查：确保是当前教师的课程
        try:
            teacher_profile = request.user.teacher_profile
            if assignment.teacher != teacher_profile:
                messages.error(request, "您只能录入自己教授课程的成绩")
                return redirect('grades:teacher-courses')
        except AttributeError:
            messages.error(request, "您没有教师权限")
            return redirect('home')
        
        # 处理成绩数据
        updated_count = 0
        error_count = 0
        
        for key, value in request.POST.items():
            if key.startswith('grade_') and value.strip():
                try:
                    student_id = int(key.replace('grade_', ''))
                    score = float(value)
                    
                    # 验证分数范围
                    if not (0 <= score <= 100):
                        error_count += 1
                        continue
                    
                    # 获取学生对象
                    student = get_object_or_404(Student, pk=student_id)
                    
                    # 验证学生是否选修了此课程
                    if not CourseEnrollment.objects.filter(
                        student=student, 
                        teaching_assignment=assignment,
                        status='ENROLLED'
                    ).exists():
                        error_count += 1
                        continue
                    
                    # 创建或更新成绩记录
                    grade, created = Grade.objects.update_or_create(
                        student=student,
                        teaching_assignment=assignment,
                        defaults={
                            'score': score,
                            'grade_type': 'FINAL',  # 默认为期末成绩
                        }
                    )
                    
                    updated_count += 1
                    
                except (ValueError, Student.DoesNotExist):
                    error_count += 1
                    continue
        
        # 显示结果消息
        if updated_count > 0:
            messages.success(request, f"成功录入/更新了 {updated_count} 条成绩记录")
        
        if error_count > 0:
            messages.warning(request, f"有 {error_count} 条记录录入失败，请检查数据格式")
        
        return redirect('grades:grade-entry', assignment_id=assignment_id)


class MyGradesView(StudentRequiredMixin, generic.ListView):
    """学生查看自己的成绩"""
    model = Grade
    template_name = 'grades/my_grades.html'
    context_object_name = 'grades_list'

    def get_queryset(self):
        """只返回当前登录学生的成绩"""
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
        
        # 获取成绩数据
        grades = context['grades_list']
        
        if grades.exists():
            # 计算基本统计信息
            total_courses = grades.count()
            graded_courses = grades.filter(score__isnull=False)
            completed_courses = graded_courses.filter(score__gte=60).count()
            
            # 计算总学分（已获得学分，即成绩>=60的课程）
            total_credits = sum(
                grade.teaching_assignment.course.credits 
                for grade in graded_courses.filter(score__gte=60)
                if grade.teaching_assignment and grade.teaching_assignment.course
            )
            
            # 计算平均分
            avg_score = graded_courses.aggregate(avg=Avg('score'))['avg']
            if avg_score:
                avg_score = round(float(avg_score), 2)
            
            # 计算加权平均分（按学分加权）
            weighted_total = 0
            credit_total = 0
            for grade in graded_courses:
                if grade.score and grade.teaching_assignment and grade.teaching_assignment.course:
                    credits = grade.teaching_assignment.course.credits
                    weighted_total += float(grade.score) * float(credits)
                    credit_total += float(credits)
            
            weighted_avg_score = round(weighted_total / credit_total, 2) if credit_total > 0 else None
            
            # 计算成绩分布
            grade_distribution = {
                'excellent': graded_courses.filter(score__gte=90).count(),  # 优秀
                'good': graded_courses.filter(score__gte=80, score__lt=90).count(),  # 良好
                'average': graded_courses.filter(score__gte=70, score__lt=80).count(),  # 中等
                'pass': graded_courses.filter(score__gte=60, score__lt=70).count(),  # 及格
                'fail': graded_courses.filter(score__lt=60).count(),  # 不及格
            }
            
            # 计算GPA统计
            gpa_grades = graded_courses.exclude(gpa__isnull=True)
            if gpa_grades.exists():
                avg_gpa = gpa_grades.aggregate(avg=Avg('gpa'))['avg']
                if avg_gpa:
                    avg_gpa = round(float(avg_gpa), 2)
                
                # 按学分加权的GPA
                weighted_gpa_total = 0
                gpa_credit_total = 0
                for grade in gpa_grades:
                    if grade.gpa and grade.teaching_assignment and grade.teaching_assignment.course:
                        credits = grade.teaching_assignment.course.credits
                        weighted_gpa_total += float(grade.gpa) * float(credits)
                        gpa_credit_total += float(credits)
                
                weighted_avg_gpa = round(weighted_gpa_total / gpa_credit_total, 2) if gpa_credit_total > 0 else None
            else:
                avg_gpa = None
                weighted_avg_gpa = None
            
            # 计算通过率
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
            
            # 按学期分组的成绩
            semester_grades = {}
            for grade in grades:
                semester = grade.teaching_assignment.semester
                if semester not in semester_grades:
                    semester_grades[semester] = []
                semester_grades[semester].append(grade)
            
            context['semester_grades'] = semester_grades
            
        else:
            # 如果没有成绩，设置默认值
            context.update({
                'total_courses': 0,
                'completed_courses': 0,
                'graded_courses': 0,
                'ungraded_courses': 0,
                'total_credits': 0,
                'average_score': None,
                'weighted_average_score': None,
                'avg_gpa': None,
                'weighted_avg_gpa': None,
                'pass_rate': 0,
                'grade_distribution': {
                    'excellent': 0,
                    'good': 0,
                    'average': 0,
                    'pass': 0,
                    'fail': 0,
                },
                'semester_grades': {},
            })
        
        return context


class GradeDeleteView(TeacherRequiredMixin, View):
    """教师删除成绩记录"""
    
    def post(self, request, grade_id):
        """删除指定的成绩记录"""
        grade = get_object_or_404(Grade, pk=grade_id)
        
        # 权限检查：确保是当前教师的课程
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
