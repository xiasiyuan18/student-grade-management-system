# student_grade_management_system/grades/frontend_urls.py
from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    # 教师成绩管理
    path('teacher/courses/', views.TeacherCoursesView.as_view(), name='teacher-courses'),
    
    # 成绩录入
    path('entry/<int:assignment_id>/', views.GradeEntryView.as_view(), name='grade-entry'),
    
    # 删除成绩
    path('delete/<int:grade_id>/', views.GradeDeleteView.as_view(), name='grade-delete'),
    
    # 学生成绩查询
    path('my-grades/', views.MyGradesView.as_view(), name='my-grades'),
]