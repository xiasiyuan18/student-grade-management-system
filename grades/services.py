from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum, Q

from courses.models import TeachingAssignment, Course
from users.models import CustomUser, Student, Teacher

from .models import Grade


def calculate_and_update_student_credits(student_profile):
    """计算并更新学生的学分信息"""
    if not isinstance(student_profile, Student):
        return
    
    student_major = student_profile.major
    student_minor_major = student_profile.minor_major
    
    # 获取所有及格的成绩记录
    passing_grades = Grade.objects.filter(
        student=student_profile,
        score__gte=60
    ).select_related('teaching_assignment__course')
    
    total_credits = 0
    major_credits = 0
    minor_credits = 0
    elective_credits = 0
    
    for grade in passing_grades:
        course = grade.teaching_assignment.course
        course_credits = course.credits
        
        if student_major and course.department == student_major.department:
            major_credits += course_credits
        elif student_minor_major and course.department == student_minor_major.department:
            minor_credits += course_credits
        else:
            elective_credits += course_credits
        
        total_credits += course_credits
    
    student_profile.credits_earned = major_credits + elective_credits
    student_profile.minor_credits_earned = minor_credits
    
    student_profile.save(update_fields=[
        'credits_earned', 
        'minor_credits_earned'
    ])
    
    return {
        'total_credits': total_credits,
        'major_credits': major_credits,
        'minor_credits': minor_credits,
        'elective_credits': elective_credits,
    }


def get_student_grade_summary(student_profile):
    """获取学生成绩汇总信息"""
    if not isinstance(student_profile, Student):
        return {}
    
    all_grades = Grade.objects.filter(
        student=student_profile
    ).select_related('teaching_assignment__course')
    
    if not all_grades.exists():
        return {
            'total_courses': 0,
            'passed_courses': 0,
            'failed_courses': 0,
            'average_score': 0,
            'gpa': 0,
            'total_credits': 0,
            'earned_credits': 0,
        }
    
    total_courses = all_grades.count()
    passed_grades = all_grades.filter(score__gte=60)
    passed_courses = passed_grades.count()
    failed_courses = total_courses - passed_courses
    
    # 计算平均分
    total_score = sum(grade.score for grade in all_grades)
    average_score = total_score / total_courses if total_courses > 0 else 0
    
    # 计算 GPA (4.0制)
    def score_to_gpa(score):
        if score >= 90:
            return 4.0
        elif score >= 80:
            return 3.0
        elif score >= 70:
            return 2.0
        elif score >= 60:
            return 1.0
        else:
            return 0.0
    
    total_gpa_points = sum(score_to_gpa(grade.score) for grade in all_grades)
    gpa = total_gpa_points / total_courses if total_courses > 0 else 0
    
    # 计算学分
    total_credits = sum(
        grade.teaching_assignment.course.credits 
        for grade in all_grades
    )
    earned_credits = sum(
        grade.teaching_assignment.course.credits 
        for grade in passed_grades
    )
    
    return {
        'total_courses': total_courses,
        'passed_courses': passed_courses,
        'failed_courses': failed_courses,
        'average_score': round(average_score, 2),
        'gpa': round(gpa, 2),
        'total_credits': total_credits,
        'earned_credits': earned_credits,
    }


def calculate_class_grade_statistics(teaching_assignment):
    """计算班级成绩统计信息"""
    grades = Grade.objects.filter(teaching_assignment=teaching_assignment)
    
    if not grades.exists():
        return {
            'total_students': 0,
            'submitted_count': 0,
            'average_score': 0,
            'highest_score': 0,
            'lowest_score': 0,
            'pass_rate': 0,
            'score_distribution': {},
        }
    
    scores = [grade.score for grade in grades]
    total_students = grades.count()
    
    average_score = sum(scores) / len(scores)
    highest_score = max(scores)
    lowest_score = min(scores)
    
    # 及格率
    passing_count = len([s for s in scores if s >= 60])
    pass_rate = (passing_count / total_students) * 100
    
    # 分数段分布
    score_distribution = {
        '90-100': len([s for s in scores if 90 <= s <= 100]),
        '80-89': len([s for s in scores if 80 <= s < 90]),
        '70-79': len([s for s in scores if 70 <= s < 80]),
        '60-69': len([s for s in scores if 60 <= s < 70]),
        '0-59': len([s for s in scores if s < 60]),
    }
    
    return {
        'total_students': total_students,
        'submitted_count': total_students,
        'average_score': round(average_score, 2),
        'highest_score': highest_score,
        'lowest_score': lowest_score,
        'pass_rate': round(pass_rate, 2),
        'score_distribution': score_distribution,
    }

def create_or_update_grade(
    student_id: int,
    teaching_assignment_id: int,
    score_value: str,
    requesting_user: CustomUser,
) -> Grade:
    """为指定学生和授课安排创建或更新成绩"""
    try:
        student = Student.objects.get(pk=student_id)
    except Student.DoesNotExist:
        raise Student.DoesNotExist(f"学号为 {student_id} 的学生不存在。")

    try:
        teaching_assignment = TeachingAssignment.objects.select_related(
            "teacher__user", "course"
        ).get(pk=teaching_assignment_id)
    except TeachingAssignment.DoesNotExist:
        raise TeachingAssignment.DoesNotExist(
            f"ID为 {teaching_assignment_id} 的授课安排不存在。"
        )

    if (
        not hasattr(requesting_user, "teacher_profile")
        or teaching_assignment.teacher != requesting_user.teacher_profile
    ):
        raise PermissionError("您没有权限为该授课安排录入或修改成绩。")

    parsed_score = None
    if score_value is not None and str(score_value).strip() != "":
        try:
            parsed_score = Decimal(str(score_value))
            if not (Decimal("0.00") <= parsed_score <= Decimal("100.00")):
                raise ValidationError("分数必须在 0.00 到 100.00 之间。")
        except InvalidOperation:
            raise ValidationError("无效的分数格式，请输入数字。")

    grade, created = Grade.objects.get_or_create(
        student=student,
        teaching_assignment=teaching_assignment,
        defaults={"score": parsed_score, "last_modified_by": requesting_user},
    )

    if not created:
        if grade.score != parsed_score:
            grade.score = parsed_score
            grade.last_modified_by = requesting_user
            grade.save()

    # 更新学分信息
    calculate_and_update_student_credits(student)

    return grade
