from django.urls import path
from . import frontend_views
from django.contrib.auth import views as auth_views
from .frontend_views import (
    TeacherListView, 
    TeacherCreateView, 
    TeacherUpdateView, 
    TeacherDeleteView,
    TeacherProfileUpdateView,
    StudentProfileUpdateView,
)
app_name = 'users'

urlpatterns = [
    # 认证URL
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # 教师管理
    path('teachers/', frontend_views.TeacherListView.as_view(), name='teacher-list'),
    path('teachers/create/', frontend_views.TeacherCreateView.as_view(), name='teacher-create'),
    path('teachers/<int:pk>/update/', frontend_views.TeacherUpdateView.as_view(), name='teacher-update'),
    path('teachers/<int:pk>/delete/', frontend_views.TeacherDeleteView.as_view(), name='teacher-delete'),

    # 学生管理
    path('students/', frontend_views.StudentListView.as_view(), name='student-list'),
    path('students/create/', frontend_views.StudentCreateView.as_view(), name='student-create'),
    
    # ✨ 关键修正：让档案编辑的URL能接收一个主键(pk)
    path('students/profile/<int:pk>/update/', frontend_views.StudentProfileUpdateView.as_view(), name='student-profile-update'),
    
    # 学生删除的URL也需要pk
    path('students/<int:pk>/delete/', frontend_views.StudentDeleteView.as_view(), name='student-delete'),
    path('profile/teacher/', TeacherProfileUpdateView.as_view(), name='teacher-profile-update'),
    path('profile/student/', StudentProfileUpdateView.as_view(), name='student-profile-update'),
]