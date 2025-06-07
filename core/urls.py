# student_grade_management_system/core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView # 用于简单的静态模板视图
from django.views.generic.base import RedirectView # 用于根路径重定向


# 导入JWT认证的token获取路由
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


urlpatterns = [
    # 1. 根路径重定向到主页 (home template)，而不是 /api/
    # 因为我们的前端是模板渲染，默认访问根路径应该看到主页
    path('', TemplateView.as_view(template_name='core/home.html'), name='home'),

    # 2. Django Admin 后台路由
    path('admin/', admin.site.urls),

    # 3. 传统 Django 模板渲染应用的 URL
    # 认证相关的模板URL
    path('accounts/', include('users.urls')), # 引入 users 应用的模板URL，带上 accounts/ 前缀

    # 包含 courses 应用的模板渲染URL
    path('courses/', include('courses.urls')), # 引入 courses 应用的模板URL

    # 包含 grades 应用的模板渲染URL  <--- 确保这一行是这样，且在 api/ 内部
    path('grades/', include('grades.urls')),   # 引入 grades 应用的模板URL


    # 4. 将所有DRF API 的路由聚合到 /api/ 下
    path('api/', include([
        # DRF 认证路由（浏览器可访问的 API 登录登出界面）
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

        # JWT认证的token获取、刷新、验证路由
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

        # 包含各个应用的 DRF ViewSets 路由
        # 这些 URL 现在指向各自应用的 urls_api.py 文件
        path("users/", include("users.urls_api")),
        path("departments/", include("departments.urls_api")),
        path("courses/", include("courses.urls_api")),
        path("grades/", include("grades.urls_api")), # <--- 引入 grades 应用的 API URL
    ])),
]