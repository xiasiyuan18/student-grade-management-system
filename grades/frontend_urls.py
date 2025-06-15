# student_grade_management_system/grades/frontend_urls.py
from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    # -- 教师功能 --
    path('teacher/courses/', views.TeacherCoursesView.as_view(), name='teacher-courses'),
    
    # ✨ 新增URL: 教师查看其课程的学生名单
    path('teacher/assignment/<int:assignment_id>/students/', views.TeacherStudentListView.as_view(), name='teacher-student-list'),
    
    # 成绩录入
    path('entry/<int:assignment_id>/', views.GradeEntryView.as_view(), name='grade-entry'),
    
    # 删除成绩 (教师用)
    path('delete/<int:grade_id>/', views.GradeDeleteView.as_view(), name='grade-delete'),
    
    # -- 学生功能 --
    path('my-grades/', views.MyGradesView.as_view(), name='my-grades'),

    # -- ✨ 新增URL: 管理员成绩管理功能 --
    path('admin/list/', views.AdminGradeListView.as_view(), name='admin-grade-list'),
    path('admin/update/<int:pk>/', views.AdminGradeUpdateView.as_view(), name='admin-grade-update'),
    path('admin/delete/<int:pk>/', views.AdminGradeDeleteView.as_view(), name='admin-grade-delete'),
]
