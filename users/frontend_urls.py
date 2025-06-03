# users/frontend_urls.py
from django.urls import path
from django.contrib.auth import views as auth_views # Django内置的认证视图
# 假设你的前端视图在 users/frontend_views.py
from . import frontend_views # 你需要在此文件中定义相应的视图类

app_name = 'users_frontend' # 定义此URL配置的命名空间

urlpatterns = [
    # --- 认证相关 URLs (由成员D负责实现对应模板和视图逻辑调整) ---
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='users/login.html'), # 模板路径 users/templates/users/login.html
        name='login' # URL名称: users_frontend:login
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='home'), # 登出后跳转到首页 (home 是在core/urls.py中定义的)
        name='logout' # URL名称: users_frontend:logout
    ),
    # 你可以在这里添加其他认证相关的URL，例如密码修改、密码重置等，
    # Django的 django.contrib.auth.urls 包含了一整套，可以考虑 include 它的一部分或全部。
    # 例如: path('password_change/', auth_views.PasswordChangeView.as_view(template_name='users/password_change_form.html', success_url=reverse_lazy('users_frontend:password_change_done')), name='password_change'),
    # path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='users/password_change_done.html'), name='password_change_done'),

    # --- 教师管理 URLs (管理员视角 - 由成员D负责实现对应视图和模板) ---
    path(
        'teachers/',
        frontend_views.TeacherListView.as_view(),
        name='teacher_list' # URL名称: users_frontend:teacher_list
    ),
    path(
        'teachers/create/',
        frontend_views.TeacherCreateView.as_view(),
        name='teacher_create' # URL名称: users_frontend:teacher_create
    ),
    path(
        'teachers/<int:pk>/update/', # pk 是 Teacher Profile 的主键 (user_id)
        frontend_views.TeacherUpdateView.as_view(),
        name='teacher_update' # URL名称: users_frontend:teacher_update
    ),
    path(
        'teachers/<int:pk>/delete/',
        frontend_views.TeacherDeleteView.as_view(),
        name='teacher_delete' # URL名称: users_frontend:teacher_delete
    ),

    # --- 学生管理 URLs (管理员视角 - 由成员B负责实现对应视图和模板) ---
    path(
        'students/',
        frontend_views.StudentListView.as_view(),
        name='student_list' # URL名称: users_frontend:student_list
    ),
    path(
        'students/create/',
        frontend_views.StudentCreateView.as_view(),
        name='student_create' # URL名称: users_frontend:student_create
    ),
    path(
        'students/<int:pk>/update/', # pk 是 Student Profile 的主键 (user_id)
        frontend_views.StudentUpdateView.as_view(),
        name='student_update' # URL名称: users_frontend:student_update
    ),
    path(
        'students/<int:pk>/delete/',
        frontend_views.StudentDeleteView.as_view(),
        name='student_delete' # URL名称: users_frontend:student_delete
    ),
    # (可选) 学生详情页，如果管理员需要查看学生档案详情
    # path(
    #     'students/<int:pk>/',
    #     frontend_views.StudentDetailView.as_view(),
    #     name='student_detail_admin_view'
    # ),


    # --- 个人信息修改 URLs ---
    # 教师修改自己的个人信息 (由成员D负责实现对应视图和模板)
    # 这个URL不需要pk，视图会根据request.user获取教师档案
    path(
        'profile/teacher/edit/',
        frontend_views.TeacherProfileSelfUpdateView.as_view(),
        name='teacher_profile_update' # URL名称: users_frontend:teacher_profile_update
    ),
    # 学生修改自己的个人信息 (由成员B负责实现对应视图和模板)
    # 这个URL不需要pk，视图会根据request.user获取学生档案
    path(
        'profile/student/edit/',
        frontend_views.StudentProfileSelfUpdateView.as_view(),
        name='student_profile_update' # URL名称: users_frontend:student_profile_update
    ),
]
