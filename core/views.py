from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.models import Student, Teacher
from departments.models import Department
from courses.models import Course, TeachingAssignment
from grades.models import Grade
from django.db.models import Count

def get_course_distribution():
    """
    获取课程选修人数分布数据。
    """
    assignments = TeachingAssignment.objects.values(
        'course__course_id', 'course__course_name'
    ).annotate(
        enrollment_count=Count('enrollments')
    ).filter(enrollment_count__gt=0).order_by('-enrollment_count')

    labels = [a['course__course_name'] for a in assignments]
    data = [a['enrollment_count'] for a in assignments]
    return {'labels': labels, 'data': data}

def get_grade_distribution():
    """
    获取全校成绩分布数据。
    """
    grades = Grade.objects.all()
    grade_ranges = {'A (90-100)': 0, 'B (80-89)': 0, 'C (70-79)': 0, 'D (60-69)': 0, 'F (<60)': 0}
    for grade in grades:
        if grade.score >= 90: grade_ranges['A (90-100)'] += 1
        elif grade.score >= 80: grade_ranges['B (80-89)'] += 1
        elif grade.score >= 70: grade_ranges['C (70-79)'] += 1
        elif grade.score >= 60: grade_ranges['D (60-69)'] += 1
        else: grade_ranges['F (<60)'] += 1
    filtered_ranges = {k: v for k, v in grade_ranges.items() if v > 0}
    return {'labels': list(filtered_ranges.keys()), 'data': list(filtered_ranges.values())}

def get_teacher_grade_distribution(teacher_user):
    """
    获取某位教师所教课程的成绩分布数据。
    这里的参数 'teacher_user' 是一个 CustomUser 实例。
    """
    # 通过 teacher__user=teacher_user 来正确地从 CustomUser 查询到对应的授课安排。
    teacher_assignments = TeachingAssignment.objects.filter(teacher__user=teacher_user)
    
    # ✨ 关键修复：直接通过授课安排(TeachingAssignment)来查找成绩。
    # Grade 模型直接关联到 TeachingAssignment，而不是 Course。
    grades = Grade.objects.filter(teaching_assignment__in=teacher_assignments)
    
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
    """
    主页视图，根据用户角色显示不同的内容。
    """
    context = {}
    user = request.user
    
    if user.is_authenticated:
        if user.is_admin:
            context.update({
                'student_count': Student.objects.count(),
                'teacher_count': Teacher.objects.count(),
                'course_count': Course.objects.count(),
                'department_count': Department.objects.count(),
                'course_distribution_data': get_course_distribution(),
                'grade_distribution_data': get_grade_distribution(),
            })
        elif user.is_teacher:
            teacher_assignments = TeachingAssignment.objects.filter(teacher__user=user)
            
            context.update({
                'teacher_courses': teacher_assignments,
                'teacher_grade_distribution_data': get_teacher_grade_distribution(user)
            })
        elif user.is_student:
            # 这里的查询是正确的，因为它通过 student Profile 关联到 user。
            context['enrollments'] = Grade.objects.filter(student__user=user)

    return render(request, 'core/home.html', context)

