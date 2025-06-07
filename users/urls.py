from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomUserViewSet,
    StudentProfileViewSet,
    TeacherProfileViewSet,
    LoginAPIView,
    LogoutAPIView
)

# ✨ 关键 #1：为API的URL设置一个独立的命名空间
app_name = 'users-api'

# 为 ViewSet 创建路由
router = DefaultRouter()
router.register(r"users", CustomUserViewSet, basename="customuser")
router.register(r"students", StudentProfileViewSet, basename="studentprofile")
router.register(r"teachers", TeacherProfileViewSet, basename="teacherprofile")

# 定义 urlpatterns
urlpatterns = [
    # 包含由 router 自动生成的 ViewSet URL
    path("", include(router.urls)),
    
    # 单独的认证相关URL
    path("auth/login/", LoginAPIView.as_view(), name="api_login"),
    
    # ✨ 关键 #2：确保登出URL的名称是 'api_logout'
    path("auth/logout/", LogoutAPIView.as_view(), name="api_logout"),
    
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]