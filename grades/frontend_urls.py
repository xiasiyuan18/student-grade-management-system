# student_grade_management_system/grades/frontend_urls.py
from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    # 成绩录入页面（教师用）
    path('entry/', views.GradeEntryView.as_view(), name='grade_entry'),
    
    # 学生查看自己成绩
    path('my-grades/', views.MyGradesView.as_view(), name='my-grades'),
    path('teacher/courses/', views.TeacherCourseListView.as_view(), name='teacher-course-list'),
]