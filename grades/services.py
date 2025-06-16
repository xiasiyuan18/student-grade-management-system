# grades/services.py
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from courses.models import TeachingAssignment
from users.models import CustomUser, Student, Teacher

from .models import Grade


def calculate_and_update_student_credits(student: Student):
    """
    重新计算并更新指定学生的已修学分（分主修和辅修）。
    当学生的任何有效成绩被创建或更新后调用此函数。
    """
    # 获取所有有效成绩（有分数的成绩）
    valid_grades = Grade.objects.filter(student=student, score__isnull=False)

    # 计算主修学分和辅修学分
    major_credits = Decimal("0.0")
    minor_credits = Decimal("0.0")
    
    if valid_grades.exists():
        for grade in valid_grades:
            if grade.teaching_assignment and grade.teaching_assignment.course:
                course = grade.teaching_assignment.course
                credits = course.credits or Decimal("0.0")
                
                # 判断是主修还是辅修课程
                if course.department == student.department:
                    # 主修院系的课程算作主修学分
                    major_credits += credits
                elif student.minor_department and course.department == student.minor_department:
                    # 辅修院系的课程算作辅修学分
                    minor_credits += credits
                else:
                    # 其他院系的课程默认算作主修学分（选修课等）
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
    student_id: int,  # 或者 student_id_num: str，取决于API传入的是主键还是业务ID
    teaching_assignment_id: int,
    score_value: str,  # 从API接收的可能是字符串
    requesting_user: CustomUser,
) -> Grade:
    """
    为指定学生和授课安排创建或更新成绩。
    由教师调用。

    Args:
        student_id: 学生的 User ID 或 Student Profile ID (这里假设是 Student Profile ID).
        teaching_assignment_id: TeachingAssignment 的 ID.
        score_value: 分数字符串，可以是空字符串或 None 表示清除分数.
        requesting_user: 执行此操作的已认证用户 (应为教师).

    Returns:
        The created or updated Grade object.

    Raises:
        Student.DoesNotExist: 如果学生不存在.
        TeachingAssignment.DoesNotExist: 如果授课安排不存在.
        PermissionError: 如果请求用户不是该授课安排的教师.
        ValidationError: 如果分数格式不正确或业务规则冲突.
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

    # 权限校验：确保操作者是该授课安排的教师
    # CustomUser (requesting_user) -> Teacher Profile (requesting_user.teacher_profile) -> TeachingAssignment
    if (
        not hasattr(requesting_user, "teacher_profile")
        or teaching_assignment.teacher != requesting_user.teacher_profile
    ):
        raise PermissionError("您没有权限为该授课安排录入或修改成绩。")

    # 处理分数
    parsed_score = None
    if score_value is not None and str(score_value).strip() != "":
        try:
            parsed_score = Decimal(str(score_value))
            if not (Decimal("0.00") <= parsed_score <= Decimal("100.00")):  # 假设百分制
                raise ValidationError("分数必须在 0.00 到 100.00 之间。")
        except InvalidOperation:
            raise ValidationError("无效的分数格式，请输入数字。")

    # 查找或创建成绩记录
    grade, created = Grade.objects.get_or_create(
        student=student,
        teaching_assignment=teaching_assignment,
        defaults={"score": parsed_score, "last_modified_by": requesting_user},
    )

    if not created:  # 如果记录已存在，则更新
        if grade.score != parsed_score:  # 只有分数变化时才更新并重新计算学分
            grade.score = parsed_score
            grade.last_modified_by = requesting_user
            grade.save()  # last_modified_time 会自动更新
        # 如果分数未变，但仍想更新 last_modified_by 和 time，可以取消 if 条件
        # else:
        #     grade.last_modified_by = requesting_user # 确保即使分数未变，操作者也被记录
        #     grade.save(update_fields=['last_modified_by', 'last_modified_time'])

    else:  # 如果是新创建的，且有分数，则需要保存后（如果 defaults 中没保存 last_modified_by 的话）
        # get_or_create 的 defaults 行为是如果创建了就直接用 defaults 的值保存
        # 所以这里不需要额外操作，除非你想在创建后立即计算学分
        pass

    # 无论创建还是更新，只要分数有效 (非 None)，就重新计算学分
    # （如果分数被设置为了 None，即删除了分数，也应该重新计算，因为该课程学分不再计入）
    calculate_and_update_student_credits(student)

    return grade
