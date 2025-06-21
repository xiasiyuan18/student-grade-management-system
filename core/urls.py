from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from .views import home 
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


urlpatterns = [
    # Django Admin 后台路由
    path('admin/', admin.site.urls),

    # Django 内置的认证路由
    path('accounts/', include('django.contrib.auth.urls')),

    # 前端页面路由
    path('', home, name='home'), 
    
    path('frontend/', include([
        path('users/', include('users.frontend_urls', namespace='users')),
        path('departments/', include('departments.frontend_urls', namespace='departments')),
        path('courses/', include('courses.frontend_urls', namespace='courses')),
        path('grades/', include('grades.frontend_urls', namespace='grades')),
        path('utils/', include('utils.urls', namespace='utils')),
    ])),

    path('query/', include('common.urls', namespace='common')),

    # 后端 API 路由
    path('api/', include([
        # DRF 认证路由（浏览器可访问的 API 登录登出界面）
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

        # JWT认证的token获取、刷新、验证路由
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

        # 包含各个应用的 DRF ViewSets 路由
        path("users/", include('users.urls', namespace='users-api')),
        path("departments/", include('departments.urls', namespace='departments-api')),
        path("courses/", include('courses.urls', namespace='courses-api')),
        path("grades/", include('grades.urls', namespace='grades-api')),
    ])),
]