from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView # 如果 StudentGradeForTeachingAssignmentView 是 APIView
from django.shortcuts import get_object_or_404

# 导入模型和序列化器
from .models import Grade
from courses.models import TeachingAssignment
from users.models import Student, CustomUser # 确保Student模型被导入

# 假设你有 GradeSerializer, StudentGradeSerializer, TeachingAssignmentGradeSerializer 等
from .serializers import GradeSerializer # 如果有 GradeViewSet

# 导入权限类，如果需要
from users.permissions import IsAdminRole, IsTeacherRole, IsStudentRole # 示例


# --- DRF ViewSet for Grade (如果存在的话) ---
class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all().order_by('student__user__username', 'teaching_assignment__semester')
    serializer_class = GradeSerializer
    # ... (其他方法和权限) ...
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated, IsAdminRole | IsTeacherRole | IsStudentRole]
        elif self.action in ['create', 'update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated, IsAdminRole | IsTeacherRole]
        elif self.action == 'destroy':
            permission_classes = [IsAdminRole]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(last_modified_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(last_modified_by=self.request.user)


# --- 针对特定授课安排的成绩列表 API 视图 ---
class TeachingAssignmentGradesListView(generics.ListAPIView): # 或者 APIView
    # 这可能是教师查看特定授课安排下所有学生成绩的API
    serializer_class = GradeSerializer # 假设用 GradeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole | IsTeacherRole]

    def get_queryset(self):
        teaching_assignment_id = self.kwargs['teaching_assignment_id']
        try:
            assignment = TeachingAssignment.objects.get(pk=teaching_assignment_id)
        except TeachingAssignment.DoesNotExist:
            return Grade.objects.none()

        queryset = Grade.objects.filter(teaching_assignment=assignment).order_by('student__user__username')

        # 权限控制：教师只能看自己授课的成绩
        user = self.request.user
        if user.is_authenticated and user.role == CustomUser.Role.TEACHER:
            if assignment.teacher != user.teacher_profile:
                return Grade.objects.none() # 教师无权访问非自己的授课

        return queryset

# --- 针对特定学生在特定授课安排下的成绩详情/修改 API 视图 ---
class StudentGradeForTeachingAssignmentView(generics.RetrieveUpdateDestroyAPIView): # 或者 APIView
    # 这可能是教师或管理员修改某个学生某个课程成绩的API
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole | IsTeacherRole] # 学生只能看自己的，管理员和教师可以修改

    def get_queryset(self):
        # 确保只能查询到自己的或有权限的成绩
        user = self.request.user
        queryset = Grade.objects.all()

        if user.is_authenticated and user.role == CustomUser.Role.STUDENT:
            # 学生只能查看自己的成绩
            return queryset.filter(student__user=user)
        elif user.is_authenticated and user.role == CustomUser.Role.TEACHER:
            # 教师只能查看自己授课的成绩
            return queryset.filter(teaching_assignment__teacher=user.teacher_profile)

        return queryset # 管理员可以看到所有

    def get_object(self):
        queryset = self.get_queryset()
        teaching_assignment_id = self.kwargs['teaching_assignment_id']
        student_id = self.kwargs['student_id']

        # 确保获取的对象是正确的
        obj = get_object_or_404(queryset,
                                teaching_assignment__pk=teaching_assignment_id,
                                student__pk=student_id)
        return obj

    def perform_update(self, serializer):
        serializer.save(last_modified_by=self.request.user)

    def perform_destroy(self, instance):
        instance.delete()