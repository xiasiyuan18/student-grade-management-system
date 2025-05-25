# departments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # 或者明确导入: from .views import DepartmentViewSet, MajorViewSet

# 创建一个 DefaultRouter 实例
router = DefaultRouter()

# 为 DepartmentViewSet 注册 URL
# 'departments' 是 URL 的前缀，例如 /api/v1/departments/
# views.DepartmentViewSet 是处理请求的视图集
# basename='department' 用于生成 URL 名称，如果你的 ViewSet 设置了 queryset，通常可以省略 basename
router.register(r'', views.DepartmentViewSet, basename='department')

# 为 MajorViewSet 注册 URL
# 'majors' 是 URL 的前缀，例如 /api/v1/majors/
router.register(r'majors', views.MajorViewSet, basename='major')

# app_name 变量可以帮助你在项目的其他地方反向解析 URL (可选，但推荐)
app_name = 'departments'

urlpatterns = [
    # 将 router 生成的 URL 模式包含进来
    path('', include(router.urls)),
]