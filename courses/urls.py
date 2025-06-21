

from django.urls import include, path
from rest_framework.routers import DefaultRouter


from .views import CourseViewSet, TeachingAssignmentViewSet


app_name = 'courses-api'

router = DefaultRouter()

router.register(r'courses', CourseViewSet, basename='course')
router.register(r'teaching-assignments', TeachingAssignmentViewSet, basename='teaching-assignment')

urlpatterns = [
    path('', include(router.urls)),
]