from django.urls import path
from .views import GradeEntryView 

app_name = 'grades'
urlpatterns = [
    path('entry/', GradeEntryView.as_view(), name='grade_entry'),
]