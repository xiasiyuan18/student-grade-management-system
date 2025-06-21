from rest_framework import serializers
from .models import Course, TeachingAssignment # 导入模型

from users.models import Teacher 
from departments.models import Department 


class CourseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.dept_name', read_only=True) # 显示关联院系名称

    class Meta:
        model = Course
        fields = '__all__' # 包含所有字段
        # 移除 read_only_fields = ('course_hours',) 因为 course_hours 属性已从模型中移除


class TeachingAssignmentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.name', read_only=True) # 假设 Teacher 有 name 字段
    course_name = serializers.CharField(source='course.course_name', read_only=True) # 假设 Course 有 course_name 字段

    class Meta:
        model = TeachingAssignment # 修正模型
        fields = '__all__'