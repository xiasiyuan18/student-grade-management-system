from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.models import Student, Teacher
from departments.models import Department
from courses.models import Course, TeachingAssignment
from grades.models import Grade
from django.db.models import Count
import json

def get_course_distribution():
    """获取热门选修课程数据 (前10名)"""
    assignments = TeachingAssignment.objects.values(
        'course__course_name'
    ).annotate(
        enrollment_count=Count('grade')
    ).filter(enrollment_count__gt=0).order_by('-enrollment_count')[:10]
    
    labels = [a['course__course_name'] for a in assignments]
    data = [a['enrollment_count'] for a in assignments]
    return {'labels': labels, 'data': data}

def get_gpa_distribution():
    """获取全校学生累计GPA分布数据"""
    gpa_brackets = {
        "3.7 ~ 4.0 (优秀)": 0, "3.0 ~ 3.6 (良好)": 0,
        "2.0 ~ 2.9 (中等)": 0, "1.0 ~ 1.9 (及格)": 0,
        "1.0 以下 (不及格)": 0,
    }
    students = Student.objects.prefetch_related(
        'grades_received', 'grades_received__teaching_assignment__course'
    )
    for student in students:
        gpa = student.calculate_cumulative_gpa()
        if gpa >= 3.7: gpa_brackets["3.7 ~ 4.0 (优秀)"] += 1
        elif gpa >= 3.0: gpa_brackets["3.0 ~ 3.6 (良好)"] += 1
        elif gpa >= 2.0: gpa_brackets["2.0 ~ 2.9 (中等)"] += 1
        elif gpa >= 1.0: gpa_brackets["1.0 ~ 1.9 (及格)"] += 1
        else: gpa_brackets["1.0 以下 (不及格)"] += 1
    return {'labels': list(gpa_brackets.keys()), 'data': list(gpa_brackets.values())}

def get_teacher_grade_distribution(teacher_user):
    """获取某位教师所教课程的成绩分布数据 (此函数供教师角色使用)"""
    teacher_assignments = TeachingAssignment.objects.filter(teacher__user=teacher_user)
    grades = Grade.objects.filter(teaching_assignment__in=teacher_assignments, score__isnull=False)
    grade_ranges = {'A (90-100)': 0, 'B (80-89)': 0, 'C (70-79)': 0, 'D (60-69)': 0, 'F (<60)': 0}
    for grade in grades:
        if grade.score >= 90: grade_ranges['A (90-100)'] += 1
        elif grade.score >= 80: grade_ranges['B (80-89)'] += 1
        elif grade.score >= 70: grade_ranges['C (70-79)'] += 1
        elif grade.score >= 60: grade_ranges['D (60-69)'] += 1
        else: grade_ranges['F (<60)'] += 1
    filtered_ranges = {k: v for k, v in grade_ranges.items() if v > 0}
    return {'labels': list(filtered_ranges.keys()), 'data': list(filtered_ranges.values())}

@login_required
def home(request):
    """主页视图，根据用户角色显示不同的内容"""
    context = {}
    user = request.user
    
    if user.is_authenticated:
        if hasattr(user, 'is_admin') and user.is_admin:
            context.update({
                'student_count': Student.objects.count(),
                'teacher_count': Teacher.objects.count(),
                'course_count': Course.objects.count(),
                'department_count': Department.objects.count(),
                'course_distribution_data': get_course_distribution(),
                'gpa_distribution_data': get_gpa_distribution(),
            })
        elif hasattr(user, 'is_teacher') and user.is_teacher:
            context['teacher_courses'] = TeachingAssignment.objects.filter(teacher__user=user)
            context['teacher_grade_distribution_data'] = get_teacher_grade_distribution(user)
        elif hasattr(user, 'is_student') and user.is_student:
            context['enrollments'] = Grade.objects.filter(student__user=user)

    return render(request, 'core/home.html', context)

