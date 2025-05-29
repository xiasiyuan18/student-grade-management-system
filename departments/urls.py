# departments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建一个 DefaultRouter 实例
router = DefaultRouter()

# **先注册 'majors'**
# 为 MajorViewSet 注册 URL
router.register(r'majors', views.MajorViewSet, basename='major')

# **再注册 '' (根路径)**
# 为 DepartmentViewSet 注册 URL
router.register(r'', views.DepartmentViewSet, basename='department')

# app_name 变量可以帮助你在项目的其他地方反向解析 URL (可选，但推荐)
app_name = 'departments'

urlpatterns = [
    # 将 router 生成的 URL 模式包含进来
    path('', include(router.urls)),
]