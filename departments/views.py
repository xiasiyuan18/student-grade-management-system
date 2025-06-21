from rest_framework import viewsets, permissions
from users.permissions import IsAdminOrReadOnly
from .models import Department, Major
from .serializers import DepartmentSerializer, MajorSerializer
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by('dept_code')
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnly]

class MajorViewSet(viewsets.ModelViewSet):
    queryset = Major.objects.all().order_by('department__dept_name', 'major_name')
    serializer_class = MajorSerializer
    permission_classes = [IsAdminOrReadOnly]