from rest_framework import viewsets, permissions
from .models import Grade
from .serializers import GradeSerializer

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all().order_by('-entry_time')
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        # 如果 last_modified_by 需要自动设置为当前用户
        if self.request.user.is_authenticated:
            serializer.save(last_modified_by=self.request.user)
        else:
            serializer.save() # 或者不允许匿名创建

    def perform_update(self, serializer):
        # 如果 last_modified_by 需要自动设置为当前用户
        if self.request.user.is_authenticated:
            serializer.save(last_modified_by=self.request.user)
        else:
            serializer.save()