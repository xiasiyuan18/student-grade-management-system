# users/frontend_urls.py (修正后)

from django.urls import path
from django.contrib.auth import views as auth_views
from . import frontend_views

# 命名空间保持为 'users'
app_name = 'users'

urlpatterns = [
    # --- 认证URL ---
    # ✨ 关键修正 #1：将登录页的 name 修改为 'login-page'，与团队约定和 Mixin 中的调用保持一致
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
    
    # ✨ 关键修正 #2：区分两个不同的“学生档案更新”URL名称
    # 这个是管理员用来编辑特定学生的档案
    path('students/profile/<int:pk>/update/', frontend_views.StudentProfileUpdateView.as_view(), name='admin-student-profile-update'),
    
    # 学生删除
    path('students/<int:pk>/delete/', frontend_views.StudentDeleteView.as_view(), name='student-delete'),
    
    # --- 个人中心 (用户自己视角) ---
    # 教师修改自己的个人信息
    path('profile/teacher/', frontend_views.TeacherProfileUpdateView.as_view(), name='teacher-profile-update'),
    
    # 学生修改自己的个人信息
    path('profile/student/', frontend_views.StudentProfileUpdateView.as_view(), name='student-profile-update'),
]