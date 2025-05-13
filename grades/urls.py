# grades/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (StudentGradeForTeachingAssignmentView,
                    TeachingAssignmentGradesListView)

# 如果有其他 Grade 的 ModelViewSet 操作 (如管理员的 CRUD)，可以放在这里
# router = DefaultRouter()
# router.register(r'grades-admin', GradeAdminViewSet, basename='grade-admin') # 假设有这个ViewSet

urlpatterns = [
    # path('', include(router.urls)), # 如果使用了上面的 router
    # 教师管理特定授课安排下的成绩
    path(
        "teaching-assignments/<int:teaching_assignment_id>/grades/",
        TeachingAssignmentGradesListView.as_view(),
        name="teaching-assignment-grades-list",
    ),
    path(
        "teaching-assignments/<int:teaching_assignment_id>/grades/students/<int:student_id>/",
        StudentGradeForTeachingAssignmentView.as_view(),
        name="student-grade-for-teaching-assignment-detail",
    ),
]
