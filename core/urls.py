# core/urls.py
from django.contrib import admin
from django.urls import path, include
# from django.views.generic.base import RedirectView

# 从您的应用中导入渲染HTML页面的视图
from users.views import UserLoginTemplateView, HomePageView # 假设您将这些视图放在users.views

from . import views as core_frontend_views

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

# --- 修改：暂时只包含已创建 frontend_urls.py 和 frontend_views.py 的应用 ---
frontend_app_urlpatterns = [
    path("users/", include("users.frontend_urls", namespace="users_frontend")),
    path("departments/", include("departments.frontend_urls", namespace="departments_frontend")), # 保留 departments
    # path("courses/", include("courses.frontend_urls", namespace="courses_frontend")), # 暂时注释掉
    # path("grades/", include("grades.frontend_urls", namespace="grades_frontend")),   # 暂时注释掉
]

urlpatterns = [
    path('', core_frontend_views.home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include([
        # 为每个应用的API都加上命名空间
        path("users/", include(("users.urls", 'users'), namespace="users")),
        path("departments/", include(("departments.urls", 'departments'), namespace="departments")),
        path("courses/", include(("courses.urls", 'courses'), namespace="courses")),
        path("grades/", include(("grades.urls", 'grades'), namespace="grades")),

        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    ])),
    path('view/', include((frontend_app_urlpatterns, 'frontend'), namespace='frontend')),
]