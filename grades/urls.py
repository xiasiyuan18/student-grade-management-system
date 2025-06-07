# student_grade_management_system/grades/urls.py

from django.urls import path
from .views import GradeEntryView # 导入用于模板渲染的视图

app_name = 'grades' # 明确定义应用命名空间，这是解决 NoReverseMatch 的关键！

urlpatterns = [
    # 教师录入/修改成绩的页面
    path('entry/', GradeEntryView.as_view(), name='grade_entry'),
    # 如果未来有学生查看成绩列表的模板页面，可以在这里添加：
    # path('my-grades/', StudentGradesListView.as_view(), name='my_grades'),
]