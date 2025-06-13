# core/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

# 导入JWT认证的token获取路由
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


urlpatterns = [
    # 1. Django Admin 后台路由
    path('admin/', admin.site.urls),

    # ====================================================================== #
    # ✨✨ 新增代码开始 ✨✨                                                   #
    # ====================================================================== #
    
    # Django 内置的认证路由 (login, logout, password_reset, 等)
    # 这会创建 /accounts/login/, /accounts/logout/ 等页面
    # 并让 {% url 'login' %} 和 {% url 'logout' %} 可以正常工作
    path('accounts/', include('django.contrib.auth.urls')),

    # ====================================================================== #
    # ✨✨ 新增代码结束 ✨✨                                                   #
    # ====================================================================== #

    # 2. 前端页面路由 (采用您的 /frontend/ 结构)
    #    根路径 '/' 直接指向前端的主页
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    #    将所有前端应用的URL聚合到 /frontend/ 下
    path('frontend/', include([
        path('users/', include('users.frontend_urls', namespace='users')),
        path('departments/', include('departments.frontend_urls', namespace='departments')),
        path('courses/', include('courses.frontend_urls', namespace='courses')),
        path('grades/', include('grades.frontend_urls', namespace='grades')),
    ])),


    # 3. 后端 API 路由 (采用队友的 /api/ 结构)
    #    将所有DRF API 的路由聚合到 /api/ 下
    path('api/', include([
        # DRF 认证路由（浏览器可访问的 API 登录登出界面）
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

        # JWT认证的token获取、刷新、验证路由
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

        # 包含各个应用的 DRF ViewSets 路由
        # 注意：这里我们假设API的路由在各自应用的 urls.py 文件中
        path("users/", include('users.urls', namespace='users-api')),
        path("departments/", include('departments.urls', namespace='departments-api')),
        path("courses/", include('courses.urls', namespace='courses-api')),
        path("grades/", include('grades.urls', namespace='grades-api')),
    ])),
]