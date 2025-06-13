# courses/frontend_urls.py (最终完整版)

from django.urls import path
# 确保从正确的文件导入了所有需要的视图
from . import frontend_views 

app_name = 'courses'

urlpatterns = [
    # 课程管理
    path('list/', frontend_views.CourseListView.as_view(), name='course-list'),
    
    # ✨ 关键修正：添加以下三行，补全创建、更新和删除的URL ✨
    path('create/', frontend_views.CourseCreateView.as_view(), name='course-create'),
    path('update/<str:pk>/', frontend_views.CourseUpdateView.as_view(), name='course-update'),
    path('delete/<str:pk>/', frontend_views.CourseDeleteView.as_view(), name='course-delete'),
]