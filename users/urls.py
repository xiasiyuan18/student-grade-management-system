# student_grade_management_system/users/urls.py
from django.urls import path
from .views import UserLoginView, UserLogoutView

app_name = 'users' # 明确定义应用命名空间

urlpatterns = [
    # 传统 Django 模板渲染的 URL
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    # 其他用户相关的模板渲染URL（如果未来有注册、个人中心等模板视图）
]