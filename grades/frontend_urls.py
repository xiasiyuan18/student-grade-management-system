# student_grade_management_system/grades/frontend_urls.py
from django.urls import path
from django.views.generic import TemplateView # 用于显示简单的静态模板

app_name = 'grades_frontend' # 定义命名空间

urlpatterns = [
    # 暂时将“我的成绩”指向一个占位模板
    path('my-grades/', TemplateView.as_view(template_name="grades/my_grades_list_placeholder.html"), name='my_grades_list'),
    # 暂时将“成绩管理”指向一个占位模板
    path('list/', TemplateView.as_view(template_name="grades/grade_list_placeholder.html"), name='grade_list'),

    # 将来您可以添加更多成绩管理的前端URL
]