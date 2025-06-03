# student_grade_management_system/courses/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CourseViewSet, TeachingAssignmentViewSet # 导入你的ViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet) # 注册CourseViewSet
router.register(r'teaching-assignments', TeachingAssignmentViewSet) # 注册TeachingAssignmentViewSet

urlpatterns = [
    path('', include(router.urls)), # 包含由router生成的URL
]