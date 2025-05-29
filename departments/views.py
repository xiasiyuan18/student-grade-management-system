# departments/views.py
from rest_framework import viewsets, permissions
# 从 users.permissions 导入 IsAdminOrReadOnly (假设你已经创建了这个文件和类)
from users.permissions import IsAdminOrReadOnly

# --- 添加或修改这一行 ---
from .models import Department, Major # <--- 从本 app 的 models.py 导入 Department 和 Major

from .serializers import DepartmentSerializer, MajorSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by('dept_code') # 现在 Department 应该被正确识别了
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnly] # 或者你为 Department 设置的权限

class MajorViewSet(viewsets.ModelViewSet):
    queryset = Major.objects.all().order_by('department__dept_name', 'major_name')
    serializer_class = MajorSerializer
    permission_classes = [IsAdminOrReadOnly] # 或者你为 Major 设置的权限