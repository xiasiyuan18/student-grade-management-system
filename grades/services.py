# grades/services.py
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from courses.models import TeachingAssignment, Course
from users.models import CustomUser, Student, Teacher

from .models import Grade


def calculate_and_update_student_credits(student: Student):
    """
    重新计算并更新指定学生的已修学分（分主修和辅修）。
    【已优化】: 1. 只计算及格成绩 (>=60分)。 2. 通过比较专业而非院系来区分主辅修。
    """
    # 【已修改】: 筛选出该学生所有及格的成绩
    passing_grades = Grade.objects.filter(student=student, score__gte=60).select_related(
        'teaching_assignment__course'
    )

    # 初始化主修和辅修学分
    major_credits = Decimal("0.0")
    minor_credits = Decimal("0.0")
    
    # 获取学生的主修和辅修专业
    student_major = student.major
    student_minor_major = student.minor_major

    if passing_grades.exists():
        for grade in passing_grades:
            # 确保关联的课程存在
            if not (grade.teaching_assignment and grade.teaching_assignment.course):
                continue

            course = grade.teaching_assignment.course
            credits = course.credits or Decimal("0.0")
            
            # 【已修改】: 通过比较专业来判断课程类型
            # 1. 检查课程是否属于辅修专业
            if student_minor_major and course.major == student_minor_major:
                minor_credits += credits
            # 2. 检查课程是否属于主修专业
            elif student_major and course.major == student_major:
                major_credits += credits
            # 3. 其他课程（如全校公选课）默认计入主修学分
            else:
                major_credits += credits

    # 更新学生的学分统计
    student.credits_earned = major_credits
    student.minor_credits_earned = minor_credits
    student.save(update_fields=["credits_earned", "minor_credits_earned"])
    
    return {
        'major_credits': major_credits,
        'minor_credits': minor_credits,
        'total_credits': major_credits + minor_credits
    }


@transaction.atomic
def create_or_update_grade(
    student_id: int,
    teaching_assignment_id: int,
    score_value: str,
    requesting_user: CustomUser,
) -> Grade:
    """
    为指定学生和授课安排创建或更新成绩。
    (此函数逻辑保持不变, 它会自动调用上面已优化的计算函数)
    """
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

    # 无论创建还是更新，都调用新的计算逻辑
    calculate_and_update_student_credits(student)

    return grade
