from django.contrib import admin
from django.urls import path, include
from . import views as core_frontend_views
from django.views.generic.base import RedirectView

login_url = RedirectView.as_view(pattern_name='users:login', permanent=False)
urlpatterns = [
    # 首页
    path('', login_url, name='home'), 
    
    # Django 自带的后台管理
    path('admin/', admin.site.urls),
    
    # --- 后端 API 路由 ---
    # 为每个应用的API分配独立的命名空间，如 'users-api'
    path('api/users/', include('users.urls', namespace='users-api')),
    path('api/departments/', include('departments.urls', namespace='departments-api')),
    # 你可以根据需要取消注释下面的行
    # path('api/courses/', include('courses.urls', namespace='courses-api')),
    # path('api/grades/', include('grades.urls', namespace='grades-api')),

    # --- 前端页面路由 ---
    # 为每个应用的前端页面分配独立的命名空间，如 'users'
    path('frontend/users/', include('users.frontend_urls', namespace='users')),
    path('frontend/departments/', include('departments.frontend_urls', namespace='departments')),
    # 你可以根据需要取消注释下面的行
    # path('frontend/courses/', include('courses.frontend_urls', namespace='courses')),
    # path('frontend/grades/', include('grades.frontend_urls', namespace='grades')),
]