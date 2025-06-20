# student_grade_management_system/grades/urls_api.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter

# 从新的 api_views 文件导入你的 DRF API 视图
from .api_views import ( # <-- 修改这一行
    StudentGradeForTeachingAssignmentView,
    TeachingAssignmentGradesListView,
    GradeViewSet # 如果有 GradeViewSet，也从这里导入
)

router = DefaultRouter()
router.register(r'grades-api', GradeViewSet, basename='grade-api') # 如果有 GradeViewSet

urlpatterns = [
    path('', include(router.urls)), # 包含 router 生成的 URL
    # 教师管理特定授课安排下的成绩 API
    path(
        "teaching-assignments/<int:teaching_assignment_id>/grades/",
        TeachingAssignmentGradesListView.as_view(),
        name="teaching-assignment-grades-list-api",
    ),
    path(
        "teaching-assignments/<int:teaching_assignment_id>/grades/students/<int:student_id>/",
        StudentGradeForTeachingAssignmentView.as_view(),
        name="student-grade-for-teaching-assignment-detail-api",
    ),
]