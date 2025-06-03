# departments/frontend_urls.py
from django.urls import path
from . import frontend_views # 你将在这个新文件中创建前端视图

app_name = 'departments_frontend'

urlpatterns = [
    path('', frontend_views.DepartmentListView.as_view(), name='department_list'),
    path('create/', frontend_views.DepartmentCreateView.as_view(), name='department_create'),
    path('<int:pk>/update/', frontend_views.DepartmentUpdateView.as_view(), name='department_update'),
    path('<int:pk>/delete/', frontend_views.DepartmentDeleteView.as_view(), name='department_delete'),

    path('majors/', frontend_views.MajorListView.as_view(), name='major_list'),
    path('majors/create/', frontend_views.MajorCreateView.as_view(), name='major_create'),
    path('majors/<int:pk>/update/', frontend_views.MajorUpdateView.as_view(), name='major_update'),
    path('majors/<int:pk>/delete/', frontend_views.MajorDeleteView.as_view(), name='major_delete'),
]