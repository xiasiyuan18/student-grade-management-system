from django.urls import path
from django.contrib.auth import views as auth_views
from . import frontend_views


app_name = 'users'

urlpatterns = [
    # --- 认证URL ---

    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login-page'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # --- 教师管理 (管理员视角) ---
    path('teachers/', frontend_views.TeacherListView.as_view(), name='teacher-list'),
    path('teachers/create/', frontend_views.TeacherCreateView.as_view(), name='teacher-create'),
    path('teachers/<int:pk>/update/', frontend_views.TeacherUpdateView.as_view(), name='teacher-update'),
    path('teachers/<int:pk>/delete/', frontend_views.TeacherDeleteView.as_view(), name='teacher-delete'),

    # --- 学生管理 (管理员视角) ---
    path('students/', frontend_views.StudentListView.as_view(), name='student-list'),
    path('students/create/', frontend_views.StudentCreateView.as_view(), name='student-create'),
    path('students/<int:pk>/update/', frontend_views.StudentUpdateView.as_view(), name='student-update'),
    path('students/<int:pk>/profile-edit/', frontend_views.StudentProfileEditView.as_view(), name='student-profile-edit'),
    path('students/<int:pk>/delete/', frontend_views.StudentDeleteView.as_view(), name='student-delete'),
    path('students/export/excel/', frontend_views.StudentExportExcelView.as_view(), name='student-export-excel'),

    # --- 个人中心 (用户自己视角) ---
    # 教师修改自己的个人信息
    path('profile/teacher/', frontend_views.TeacherProfileUpdateView.as_view(), name='teacher-profile-update'),
    
    # 学生修改自己的个人信息
    path('profile/student/', frontend_views.StudentProfileUpdateView.as_view(), name='student-profile-update'),
]