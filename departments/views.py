# departments/views.py
from rest_framework import viewsets, permissions
from .models import Department, Major
from .serializers import DepartmentSerializer, MajorSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by('dept_code')
    serializer_class = DepartmentSerializer
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly] # 示例，根据需求调整
    # 具体的权限由成员D统一规划和实现

class MajorViewSet(viewsets.ModelViewSet):
    queryset = Major.objects.all().order_by('department__dept_name', 'major_name')
    serializer_class = MajorSerializer
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly]