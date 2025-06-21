from django.urls import path
from . import views

app_name = 'utils'

urlpatterns = [
    path(
        'import/students/', 
        views.StudentImportView.as_view(), 
        name='student-bulk-import'
    ),
]
    