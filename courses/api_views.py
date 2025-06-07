# student_grade_management_system/courses/api_views.py
from rest_framework import viewsets, permissions
from rest_framework import serializers # 如果你的serializers有用到

# 导入自定义权限 (假设你之前已创建 users/permissions.py)
# 根据你的项目实际情况，如果权限在 users.permissions，确保路径正确
from users.permissions import IsAdminOrReadOnly # 假设权限在此

# 导入模型
from .models import Course, TeachingAssignment
# 导入序列化器 (假设它们存在于 courses/serializers.py)
from .serializers import CourseSerializer, TeachingAssignmentSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('course_id')
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly] # 示例权限


class TeachingAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TeachingAssignment.objects.all().order_by('semester', 'course__course_name')
    serializer_class = TeachingAssignmentSerializer
    permission_classes = [IsAdminOrReadOnly] # 示例权限