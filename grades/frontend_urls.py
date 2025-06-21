from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    # -- 教师功能 --
    path('teacher/courses/', views.TeacherCoursesView.as_view(), name='teacher-courses'),
    path('teacher/assignment/<int:assignment_id>/students/', views.TeacherStudentListView.as_view(), name='teacher-student-list'),
    path('entry/<int:assignment_id>/', views.GradeEntryView.as_view(), name='grade-entry'),
    path('delete/<int:grade_id>/', views.GradeDeleteView.as_view(), name='grade-delete'),
    
    # -- 学生功能 --
    path('my-grades/', views.MyGradesView.as_view(), name='my-grades'),
    path('admin/list/', views.AdminGradeListView.as_view(), name='admin-grade-list'),
    path('admin/update/<int:pk>/', views.AdminGradeUpdateView.as_view(), name='admin-grade-update'),
    path('admin/delete/<int:pk>/', views.AdminGradeDeleteView.as_view(), name='admin-grade-delete'),
]
