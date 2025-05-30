# student_grade_management_system/courses/views.py
from rest_framework import viewsets, permissions
from rest_framework import serializers 

# 导入自定义权限 (假设你之前已创建 users/permissions.py)
from users.permissions import IsAdminOrReadOnly 

# 导入模型
from .models import Course, TeachingAssignment 
# 导入序列化器 (假设它们存在于 courses/serializers.py)
from .serializers import CourseSerializer, TeachingAssignmentSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('course_id')
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly] 


class TeachingAssignmentViewSet(viewsets.ModelViewSet): 
    queryset = TeachingAssignment.objects.all().order_by('semester', 'course__course_name') 
    serializer_class = TeachingAssignmentSerializer
    permission_classes = [IsAdminOrReadOnly]