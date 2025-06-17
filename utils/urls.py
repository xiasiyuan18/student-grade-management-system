# utils/urls.py

from django.urls import path
from . import views

app_name = 'utils'

urlpatterns = [
    # 将这里的 views.StudentBulkImportView 修改为 views.StudentImportView
    path(
        'import/students/', 
        views.StudentImportView.as_view(), 
        name='student-bulk-import'
    ),
]
    