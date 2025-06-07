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

router = DefaultRouter()
router.register(r"users", CustomUserViewSet, basename="customuser")
router.register(r"students", StudentProfileViewSet, basename="studentprofile")
router.register(r"teachers", TeacherProfileViewSet, basename="teacherprofile")

urlpatterns = [
    # 包含由 router 自动生成的 ViewSet URL
    path("", include(router.urls)),
    # 单独的认证相关API URL (例如 /api/users/auth/login/)
    path("auth/login/", LoginAPIView.as_view(), name="api_login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="api_logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),
    # 您可能还会有其他用户相关的API URL
]