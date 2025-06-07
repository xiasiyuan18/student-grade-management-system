# student_grade_management_system/courses/urls_api.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

# 从新的 api_views 文件导入 ViewSets
from .api_views import CourseViewSet, TeachingAssignmentViewSet # <-- 修改这一行

router = DefaultRouter()
router.register(r"courses", CourseViewSet)
router.register(r"teaching-assignments", TeachingAssignmentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]