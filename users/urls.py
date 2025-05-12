from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet

router = DefaultRouter()
router.register(r'students', StudentViewSet) # 端点会是 /api/users/students/

urlpatterns = [
    path('', include(router.urls)),
]




from .views import TeacherViewSet # , LoginAPIView, LogoutAPIView # 如果登录视图也在此文件中

router = DefaultRouter()
router.register(r'teachers', TeacherViewSet, basename='teacher') # 'teachers' 是URL前缀, 'teacher' 是basename用于生成URL名称

urlpatterns = [
    path('', include(router.urls)), # 包含ViewSet生成的URL
    # path('auth/login/', LoginAPIView.as_view(), name='api_login'), # 您之前设计的登录API
    # path('auth/logout/', LogoutAPIView.as_view(), name='api_logout'), # 您之前设计的登出API
]