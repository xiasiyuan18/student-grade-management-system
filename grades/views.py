# grades/views.py
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics, permissions, status, views
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from courses.models import TeachingAssignment
from users.models import CustomUser, Student, Teacher

from .models import Grade
from .serializers import GradeSerializer, GradeUpdateSerializer
from .services import (calculate_and_update_student_credits,
                       create_or_update_grade)


class IsTeacher(permissions.BasePermission):
    """
    自定义权限，只允许教师访问。
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == CustomUser.Role.TEACHER
        )


class IsStudentRole(permissions.BasePermission):
    """
    自定义权限，只允许学生访问。
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == CustomUser.Role.STUDENT
        )


# API 端点: /api/teaching-assignments/{teaching_assignment_id}/grades/
# 这个端点用于教师管理其特定授课安排下的学生成绩


class TeachingAssignmentGradesListView(views.APIView):
    """
    列出某个授课安排下所有学生的成绩，并允许教师为该安排下的学生批量录入/更新成绩。
    GET: /api/teaching-assignments/{teaching_assignment_id}/grades/
         - 教师获取其特定授课安排下所有已存在的成绩记录。
    POST: /api/teaching-assignments/{teaching_assignment_id}/grades/ (或者用PUT更符合更新单个资源)
          - （此端点可能更适合批量更新，但逐个更新更符合我们当前的service）
          - 我们将创建一个专门的端点用于单个学生成绩的更新/创建。
    """

    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_teaching_assignment(self, pk, user: CustomUser):
        try:
            assignment = TeachingAssignment.objects.get(pk=pk)
            # 权限校验：确保教师是该授课安排的负责人
            if (
                not hasattr(user, "teacher_profile")
                or assignment.teacher != user.teacher_profile
            ):
                raise DRFPermissionDenied("您没有权限访问此授课安排的成绩。")
            return assignment
        except TeachingAssignment.DoesNotExist:
            raise NotFound(detail="指定的授课安排不存在。")

    def get(self, request, teaching_assignment_id, *args, **kwargs):
        """
        教师获取其特定授课安排下所有已存在的成绩记录。
        """
        teaching_assignment = self.get_teaching_assignment(
            teaching_assignment_id, request.user
        )

        # 获取与此授课安排相关的所有成绩记录
        grades = Grade.objects.filter(
            teaching_assignment=teaching_assignment
        ).select_related(
            "student__user",  # 优化查询，获取学生基本用户数据
            "student__major",  # 假设需要显示专业
            "student__department",  # 假设需要显示院系
            "teaching_assignment__course",
            "teaching_assignment__teacher__user",
            "last_modified_by",
        )
        serializer = GradeSerializer(grades, many=True)
        return Response(serializer.data)


# API 端点: /api/teaching-assignments/{teaching_assignment_id}/grades/students/{student_id}/
class StudentGradeForTeachingAssignmentView(views.APIView):
    """
    教师为特定授课安排下的特定学生录入、修改或查看成绩。
    GET: 获取单个学生的成绩信息。
    PUT: 创建或更新单个学生的成绩。
    """

    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_teaching_assignment_and_student(
        self, teaching_assignment_id, student_id, user: CustomUser
    ):
        try:
            assignment = TeachingAssignment.objects.select_related("teacher__user").get(
                pk=teaching_assignment_id
            )
            if (
                not hasattr(user, "teacher_profile")
                or assignment.teacher != user.teacher_profile
            ):
                raise DRFPermissionDenied("您没有权限操作此授课安排的成绩。")
        except TeachingAssignment.DoesNotExist:
            raise NotFound(detail="指定的授课安排不存在。")

        try:
            # 注意：这里传入的 student_id 是 Student Profile 的 PK
            student = Student.objects.get(
                user_id=student_id
            )  # 或者 pk=student_id，如果student_id就是Student的PK
        except Student.DoesNotExist:
            raise NotFound(detail="指定的学生不存在。")

        return assignment, student

    def get(self, request, teaching_assignment_id, student_id, *args, **kwargs):
        """
        教师获取特定授课安排下特定学生的成绩。
        """
        teaching_assignment, student = self.get_teaching_assignment_and_student(
            teaching_assignment_id, student_id, request.user
        )

        try:
            grade = Grade.objects.get(
                teaching_assignment=teaching_assignment, student=student
            )
            serializer = GradeSerializer(grade)
            return Response(serializer.data)
        except Grade.DoesNotExist:
            # 如果成绩不存在，可以返回 404 或一个表示“未录入”的空对象
            # return Response({"detail": "该学生在此授课安排下尚无成绩记录。"}, status=status.HTTP_404_NOT_FOUND)
            # 或者前端可以理解为：获取不到就代表可以创建
            # 或者返回一个预填充部分信息的对象，方便前端录入
            return Response(
                {
                    "student_id": student.pk,  # Student Profile PK
                    "teaching_assignment_id": teaching_assignment.pk,
                    "score": None,
                    "detail": "成绩未录入",
                },
                status=status.HTTP_200_OK,
            )  # 或者 HTTP_404_NOT_FOUND 如果前端严格区分

    def put(self, request, teaching_assignment_id, student_id, *args, **kwargs):
        """
        教师为特定授课安排下的特定学生创建或更新成绩。
        请求体应包含 'score'。
        """
        teaching_assignment, student = self.get_teaching_assignment_and_student(
            teaching_assignment_id, student_id, request.user
        )

        serializer = GradeUpdateSerializer(data=request.data)
        if serializer.is_valid():
            score_value = serializer.validated_data.get("score")  # 这是字符串或None

            try:
                # student_id 来自 URL，teaching_assignment_id 来自 URL
                # 注意 service 函数期望的 student_id 是 Student Profile 的 PK
                grade_instance = create_or_update_grade(
                    student_id=student.pk,
                    teaching_assignment_id=teaching_assignment.pk,
                    score_value=score_value,
                    requesting_user=request.user,
                )
                response_serializer = GradeSerializer(grade_instance)
                return Response(
                    response_serializer.data, status=status.HTTP_200_OK
                )  # 也可以是 HTTP_201_CREATED 如果是新创建的
            except DjangoValidationError as e:
                raise DRFValidationError(detail=e.messages)
            except DjangoPermissionDenied as e:
                raise DRFPermissionDenied(detail=str(e))
            except (
                Student.DoesNotExist,
                TeachingAssignment.DoesNotExist,
            ) as e:  # Service层已抛出，这里捕获以返回标准DRF错误
                raise NotFound(detail=str(e))
            except Exception as e:  # 其他未知错误
                # Log this exception
                return Response(
                    {"detail": "处理成绩时发生内部错误。"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class MyGradesListView(generics.ListAPIView):
    """
    学生查询自己所有成绩的视图。
    GET: /api/grades/my-grades/
    """
    serializer_class = GradeSerializer
    # 权限设置为：必须是已认证用户，且角色必须是学生
    permission_classes = [permissions.IsAuthenticated, IsStudentRole]

    def get_queryset(self):
        """
        此视图只返回当前登录学生用户的所有成绩记录。
        """
        user = self.request.user
        # 通过 user -> student_profile -> grades_received 反向查询
        return Grade.objects.filter(student__user=user).select_related(
            'student',
            'teaching_assignment__course',
            'teaching_assignment__teacher'
        ).order_by('-teaching_assignment__semester') # 按学期降序排列