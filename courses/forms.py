# student_grade_management_system/courses/forms.py
from django import forms
from .models import Course, TeachingAssignment

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__' # 包含所有字段
        # 也可以明确指定字段，例如：fields = ['course_id', 'course_name', 'description', 'credits', 'degree_level', 'department']
        widgets = {
            'course_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入课程编号'}),
            'course_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入课程名称'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入课程说明'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '请输入学分'}),
            'degree_level': forms.Select(attrs={'class': 'form-select'}), # 下拉选择框
            'department': forms.Select(attrs={'class': 'form-select'}), # 下拉选择框
        }
        labels = {
            'course_id': '课程编号',
            'course_name': '课程名称',
            'description': '课程说明',
            'credits': '学分',
            'degree_level': '学位等级',
            'department': '开课院系',
        }
        help_texts = {
            'course_id': '课程的唯一编号 (3-20字符)',
            'credits': '课程的学分 (0.0-30.0)',
        }

class TeachingAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeachingAssignment
        fields = '__all__'
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例如: 2024 Fall'}),
        }
        labels = {
            'teacher': '授课教师',
            'course': '所授课程',
            'semester': '学期',
        }
        help_texts = {
            'semester': '授课发生的学期，例如 2024 Fall',
        }