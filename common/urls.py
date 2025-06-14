from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    # 通用查询功能
    path('departments/', views.DepartmentListView.as_view(), name='department-list'),
    path('majors/', views.MajorListView.as_view(), name='major-list'),
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('teachers/', views.TeacherInfoListView.as_view(), name='teacher-list'),
    
    # 学生个人信息
    path('student/info/', views.StudentInfoView.as_view(), name='student-info'),
]