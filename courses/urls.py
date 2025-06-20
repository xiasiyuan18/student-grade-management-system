# courses/urls.py (最终正确版，用于API)

from django.urls import include, path
from rest_framework.routers import DefaultRouter

# ✨ 关键修正：从正确的 API 视图文件 (views.py) 导入 ✨
from .views import CourseViewSet, TeachingAssignmentViewSet

# 根据团队多数人约定，这个文件用于 API，我们可以统一API的命名空间
app_name = 'courses-api'

router = DefaultRouter()
# 为了和URL name风格统一，这里也建议使用连字符
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'teaching-assignments', TeachingAssignmentViewSet, basename='teaching-assignment')

urlpatterns = [
    path('', include(router.urls)),
]