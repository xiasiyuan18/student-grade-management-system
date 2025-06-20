# courses/frontend_urls.py (完整版)

from django.urls import path
from . import frontend_views

app_name = 'courses'

urlpatterns = [
    # 课程管理
    path('', frontend_views.CourseListView.as_view(), name='course-list'),
    path('create/', frontend_views.CourseCreateView.as_view(), name='course-create'),
    path('<str:pk>/update/', frontend_views.CourseUpdateView.as_view(), name='course-update'),
    path('<str:pk>/delete/', frontend_views.CourseDeleteView.as_view(), name='course-delete'),
    
    # 授课安排管理
    path('teaching-assignments/', frontend_views.TeachingAssignmentListView.as_view(), name='teaching-assignment-list'),
    path('teaching-assignments/create/', frontend_views.TeachingAssignmentCreateView.as_view(), name='teaching-assignment-create'),
    path('teaching-assignments/<int:pk>/update/', frontend_views.TeachingAssignmentUpdateView.as_view(), name='teaching-assignment-update'),
    path('teaching-assignments/<int:pk>/delete/', frontend_views.TeachingAssignmentDeleteView.as_view(), name='teaching-assignment-delete'),
    
    # 选课管理
    path('enrollments/', frontend_views.CourseEnrollmentListView.as_view(), name='enrollment-list'),
    path('enrollments/create/', frontend_views.CourseEnrollmentCreateView.as_view(), name='enrollment-create'),
    path('enrollments/<int:pk>/update/', frontend_views.CourseEnrollmentUpdateView.as_view(), name='enrollment-update'),
    path('enrollments/<int:pk>/delete/', frontend_views.CourseEnrollmentDeleteView.as_view(), name='enrollment-delete'),
    path('enrollments/bulk/', frontend_views.BulkEnrollmentView.as_view(), name='bulk-enrollment'),
]