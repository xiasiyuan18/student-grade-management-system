from django.urls import include, path
from rest_framework.routers import DefaultRouter


from .api_views import ( 
    StudentGradeForTeachingAssignmentView,
    TeachingAssignmentGradesListView,
    GradeViewSet
)

router = DefaultRouter()
router.register(r'grades-api', GradeViewSet, basename='grade-api') 

urlpatterns = [
    path('', include(router.urls)), 
    path(
        "teaching-assignments/<int:teaching_assignment_id>/grades/",
        TeachingAssignmentGradesListView.as_view(),
        name="teaching-assignment-grades-list-api",
    ),
    path(
        "teaching-assignments/<int:teaching_assignment_id>/grades/students/<int:student_id>/",
        StudentGradeForTeachingAssignmentView.as_view(),
        name="student-grade-for-teaching-assignment-detail-api",
    ),
]