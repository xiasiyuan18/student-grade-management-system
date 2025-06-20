# student_grade_management_system/courses/admin.py
from django.contrib import admin
from .models import Course, TeachingAssignment # 确保导入了正确的模型类 (TeachingAssignment)

# 注册 Course 模型到 Admin 后台
@admin.register(Course) 
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'course_name', 'credits', 'department') 
    search_fields = ('course_id', 'course_name') 
    ordering = ('course_id',) 
    list_filter = ('department', 'degree_level') 

# 注册 TeachingAssignment 模型到 Admin 后台
@admin.register(TeachingAssignment) 
class TeachingAssignmentAdmin(admin.ModelAdmin): 
    list_display = ('teacher', 'course', 'semester') 
    search_fields = ('teacher__name', 'course__course_name', 'semester') 
    list_filter = ('semester', 'teacher', 'course') 
    raw_id_fields = ('teacher', 'course')