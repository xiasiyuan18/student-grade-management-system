from rest_framework import viewsets, permissions
from .models import Student
from .serializers import StudentSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().order_by('student_id')
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # 或者 IsAdminUser 来限制访问
    # permission_classes = [permissions.AllowAny] # 出于演示目的，更宽松，生产环境请谨慎