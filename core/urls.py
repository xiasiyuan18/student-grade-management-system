# student_grade_management_system/core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView 

# 导入JWT认证的token获取路由
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


urlpatterns = [
    # 1. 根路径重定向到 /api/，方便浏览器访问
    path('', RedirectView.as_view(url='/api/', permanent=False)), 

    # 2. Django Admin 后台路由
    path('admin/', admin.site.urls), 

    # 3. 将所有DRF ViewSets 的路由聚合到 /api/ 下
    # 错误：之前是 path("api/users/", include("users.urls")), 等，它们会匹配 api/users/ 而不是 api/
    # 正确：现在需要创建一个统一的 /api/ 根路由，然后包含所有应用的路由
    path('api/', include([
        path("users/", include("users.urls")),        
        path("departments/", include("departments.urls")), 
        path("courses/", include("courses.urls")), 
        path("grades/", include("grades.urls")),   
        # DRF 认证路由
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')), 
        # JWT认证的token获取、刷新、验证路由
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    ])),
]
