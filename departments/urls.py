# departments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建一个 DefaultRouter 实例
router = DefaultRouter()

router.register(r'majors', views.MajorViewSet, basename='major')

router.register(r'', views.DepartmentViewSet, basename='department')

app_name = 'departments'

urlpatterns = [
    path('', include(router.urls)),
]