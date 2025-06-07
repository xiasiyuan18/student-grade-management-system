# student_grade_management_system/courses/urls.py
from django.urls import path
from .views import (
    CourseListView,
    CourseCreateView,
    CourseUpdateView,
    CourseDeleteView,
)

app_name = 'courses' # 定义应用命名空间，非常重要！

urlpatterns = [
    # 课程管理（管理员视角）
    path('list/', CourseListView.as_view(), name='course_list'),
    path('create/', CourseCreateView.as_view(), name='course_create'),
    path('update/<str:pk>/', CourseUpdateView.as_view(), name='course_update'), # Course 的主键是 course_id (str)
    path('delete/<str:pk>/', CourseDeleteView.as_view(), name='course_delete'),
    # 如果未来需要 TeachingAssignment 的模板管理视图，可以类似地在这里添加
    # path('assignments/list/', TeachingAssignmentListView.as_view(), name='assignment_list'),
    # path('assignments/create/', TeachingAssignmentCreateView.as_view(), name='assignment_create'),
]