from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet  # 假设你创建了 CustomUserViewSet
from .views import \
    StudentProfileViewSet  # 假设你将 StudentViewSet 重命名或创建为 StudentProfileViewSet
from .views import \
    TeacherProfileViewSet  # LoginView,            # 假设的登录视图; LogoutView,           # 假设的登出视图; RegisterView          # 假设的注册视图; 假设你创建了 TeacherProfileViewSet


# dj_rest_auth 提供了更全面的认证URL，如果使用它，可以这样包含：
# urlpatterns = [
#     path('auth/', include('dj_rest_auth.urls')),
#     path('auth/registration/', include('dj_rest_auth.registration.urls')), # 如果使用注册功能
# ]
# 如果你手动实现登录/登出，可以像下面这样定义：
# urlpatterns = [
#     path('auth/login/', LoginView.as_view(), name='user-login'),
#     path('auth/logout/', LogoutView.as_view(), name='user-logout'),
#     # path('auth/register/', RegisterView.as_view(), name='user-register'), # 如果有注册
# ]

# 使用 Router 注册 ModelViewSet
router = DefaultRouter()
router.register(
    r"users", CustomUserViewSet, basename="customuser"
)  # 管理 CustomUser 账户
router.register(
    r"students", StudentProfileViewSet, basename="studentprofile"
)  # 管理 Student Profiles
router.register(
    r"teachers", TeacherProfileViewSet, basename="teacherprofile"
)  # 管理 Teacher Profiles

# 将 router 生成的 URL 和其他自定义的 URL 合并
urlpatterns = [
    path("", include(router.urls)),
    # 如果你使用 dj_rest_auth，则在此处添加它的 include 语句，或者上面已经添加
    # 如果你手动实现了登录/登出/注册视图，将它们的 path() 添加在这里
    # 例如：
    # path('auth/login/', YourLoginView.as_view(), name='login'),
    # path('auth/logout/', YourLogoutView.as_view(), name='logout'),
]

# 如果你的登录/注册等视图不是 ViewSet，而是普通的 APIView，
# 并且你想把它们也放在这个 users/urls.py 下，可以这样：
# from .views import LoginAPI, RegisterAPI # 假设你有这些视图
# urlpatterns += [
#     path('login/', LoginAPI.as_view(), name='login'),
#     path('register/', RegisterAPI.as_view(), name='register'),
# ]


# 如果使用 djangorestframework-simplejwt 并希望提供刷新token的端点
from rest_framework_simplejwt.views import TokenRefreshView

# 导入您在 users/views.py 中创建的视图
from .views import CustomUserViewSet  # 管理 CustomUser 的 ViewSet
from .views import \
    StudentProfileViewSet  # 假设成员B的 StudentProfileViewSet 也在这里或您已创建
from .views import LoginAPIView  # 或者您命名的 LoginAPIView
from .views import LogoutAPIView, TeacherProfileViewSet

# 为 ViewSet 创建路由
router = DefaultRouter()
router.register(
    r"users", CustomUserViewSet, basename="customuser"
)  # URL: /api/users/users/
router.register(
    r"students", StudentProfileViewSet, basename="studentprofile"
)  # URL: /api/users/students/
router.register(
    r"teachers", TeacherProfileViewSet, basename="teacherprofile"
)  # URL: /api/users/teachers/
# 注意：上面的 URL 前缀是相对于 "api/users/" 的，所以完整路径会是 /api/users/users/, /api/users/students/ 等

# 定义 urlpatterns
urlpatterns = [
    # 包含由 router 自动生成的 ViewSet URL
    path("", include(router.urls)),
    # 单独的认证相关URL
    path("auth/login/", LoginAPIView.as_view(), name="api_login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="api_logout"),
    # (可选) 如果使用 Simple JWT 并希望提供刷新 access token 的端点
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # 您可能还会有其他用户相关的URL，例如注册、密码修改等
    # path('auth/register/', RegisterAPIView.as_view(), name='api_register'),
    # path('auth/password/change/', ChangePasswordView.as_view(), name='api_password_change'),
]