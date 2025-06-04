# student_grade_management_system/courses/frontend_urls.py
from django.urls import path
from django.views.generic import TemplateView # 用于显示简单的静态模板

app_name = 'courses_frontend' # 定义命名空间，与您模板中的 'courses_frontend' 对应

urlpatterns = [
    # 暂时将课程列表指向一个占位模板
    # 您以后可以将 TemplateView 替换为实际的课程列表视图
    path('list/', TemplateView.as_view(template_name="courses/course_list_placeholder.html"), name='course_list'),

    # 将来您可以添加更多课程管理的前端URL，例如：
    # path('create/', views.course_create_view, name='course_create'),
    # path('<int:pk>/update/', views.course_update_view, name='course_update'),
    # path('<int:pk>/delete/', views.course_delete_view, name='course_delete'),
]