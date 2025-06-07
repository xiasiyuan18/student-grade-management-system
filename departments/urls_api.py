# student_grade_management_system/departments/urls_api.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

# 假设你的 departments/views.py 中有以下 ViewSets
# 如果没有，或者名字不同，你需要根据实际情况修改
from .views import DepartmentViewSet, MajorViewSet # 导入你的 ViewSets

router = DefaultRouter()
router.register(r"departments", DepartmentViewSet) # 注册 DepartmentViewSet
router.register(r"majors", MajorViewSet)           # 注册 MajorViewSet

urlpatterns = [
    path("", include(router.urls)), # 包含由 router 自动生成的 URL
    # 如果部门或专业有其他独立的API视图，可以在这里添加
]