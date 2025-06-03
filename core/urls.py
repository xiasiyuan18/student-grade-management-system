# core/urls.py
from django.contrib import admin
from django.urls import path, include
# from django.views.generic.base import RedirectView

from . import views as core_frontend_views

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

# --- 修改：暂时只包含已创建 frontend_urls.py 和 frontend_views.py 的应用 ---
frontend_app_urlpatterns = [
    # path("users/", include("users.frontend_urls", namespace="users_frontend")), # 暂时注释掉 users 的前端URLs
    path("departments/", include("departments.frontend_urls", namespace="departments_frontend")), # 保留 departments
    # path("courses/", include("courses.frontend_urls", namespace="courses_frontend")), # 暂时注释掉
    # path("grades/", include("grades.frontend_urls", namespace="grades_frontend")),   # 暂时注释掉
]

urlpatterns = [
    path('', core_frontend_views.home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include([
        path("users/", include("users.urls")),
        path("departments/", include("departments.urls")),
        path("courses/", include("courses.urls")),
        path("grades/", include("grades.urls")),
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    ])),
    path('view/', include((frontend_app_urlpatterns, 'frontend'), namespace='frontend')),
]