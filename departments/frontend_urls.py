from django.urls import path
from . import frontend_views

# 关键: 前端页面的应用名是 'departments'
app_name = 'departments'

urlpatterns = [
    path('departments/', frontend_views.DepartmentListView.as_view(), name='department-list'),
    path('departments/create/', frontend_views.DepartmentCreateView.as_view(), name='department-create'),
    path('departments/<int:pk>/update/', frontend_views.DepartmentUpdateView.as_view(), name='department-update'),
    path('departments/<int:pk>/delete/', frontend_views.DepartmentDeleteView.as_view(), name='department-delete'),
    
    path('majors/', frontend_views.MajorListView.as_view(), name='major-list'),
    path('majors/create/', frontend_views.MajorCreateView.as_view(), name='major-create'),
    path('majors/<int:pk>/update/', frontend_views.MajorUpdateView.as_view(), name='major-update'),
    path('majors/<int:pk>/delete/', frontend_views.MajorDeleteView.as_view(), name='major-delete'),
]