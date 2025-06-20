# courses/views.py (这个文件用于后端API视图)

from rest_framework import viewsets, permissions
from .models import Course, TeachingAssignment
from .serializers import CourseSerializer, TeachingAssignmentSerializer

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('course_id')
    serializer_class = CourseSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser] 
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

class TeachingAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TeachingAssignment.objects.all().order_by('semester', 'course__course_name')
    serializer_class = TeachingAssignmentSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]