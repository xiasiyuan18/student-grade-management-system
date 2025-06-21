# departments/frontend_urls.py (连字符 '-' 统一版)

from django.urls import path
from . import frontend_views

app_name = 'departments'

urlpatterns = [
    # 院系管理 - 如果Department模型的主键不是默认的id，需要相应调整
    path('', frontend_views.DepartmentListView.as_view(), name='department-list'),
    path('create/', frontend_views.DepartmentCreateView.as_view(), name='department-create'),
    
    # 如果Department使用dept_id作为主键，并且可能包含特殊字符
    path('<slug:pk>/update/', frontend_views.DepartmentUpdateView.as_view(), name='department-update'),
    path('<slug:pk>/delete/', frontend_views.DepartmentDeleteView.as_view(), name='department-delete'),
    
    # 专业管理
    path('majors/', frontend_views.MajorListView.as_view(), name='major-list'),
    path('majors/create/', frontend_views.MajorCreateView.as_view(), name='major-create'),
    path('majors/<slug:pk>/update/', frontend_views.MajorUpdateView.as_view(), name='major-update'),
    path('majors/<slug:pk>/delete/', frontend_views.MajorDeleteView.as_view(), name='major-delete'),
]