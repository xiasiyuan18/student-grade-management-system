from rest_framework import viewsets, permissions
from .models import Student
from .serializers import StudentSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().order_by('student_id')
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # 或者 IsAdminUser 来限制访问
    # permission_classes = [permissions.AllowAny] # 出于演示目的，更宽松，生产环境请谨慎

from .models import Teacher
from .serializers import TeacherSerializer

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all().order_by('teacher_id')
    serializer_class = TeacherSerializer
    permission_classes = [permissions.IsAuthenticated] # 默认需要认证才能访问
    # 您需要根据您的权限设计来设置 permission_classes
    # 例如，教师可能只能修改自己的信息，管理员可以修改所有教师信息
