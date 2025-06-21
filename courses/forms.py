from django import forms
from .models import Course, TeachingAssignment
from users.models import Teacher
from departments.models import Department
from users.models import Student  

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__' 
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
    """创建和编辑授课安排的表单"""
    
    class Meta:
        model = TeachingAssignment
        fields = ['teacher', 'course', 'semester']  # 只使用实际存在的字段
        labels = {
            'teacher': '授课教师',
            'course': '课程',
            'semester': '学期',
        }
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '如：2024 Fall'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = Teacher.objects.select_related('user', 'department')

        self.fields['teacher'].label_from_instance = self.get_teacher_display
        
        
        self.fields['course'].queryset = Course.objects.select_related('department')
        
        self.fields['course'].label_from_instance = self.get_course_display

    def get_teacher_display(self, obj):
        """安全地获取教师显示信息"""
        try:
            dept_name = getattr(obj.department, 'dept_name', None) or getattr(obj.department, 'department_name', '未知院系')
            return f"{obj.name} ({obj.teacher_id_num}) - {dept_name}"
        except Exception:
            return f"{obj.name} ({obj.teacher_id_num})"

    def get_course_display(self, obj):
        """安全地获取课程显示信息"""
        try:
            dept_name = getattr(obj.department, 'dept_name', None) or getattr(obj.department, 'department_name', '未知院系')
            return f"{obj.course_name} ({obj.course_id}) - {dept_name}"
        except Exception:
            return f"{obj.course_name} ({obj.course_id})"

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'student_id_num', 'name', 'id_card', 'gender', 'birth_date',
            'phone', 'dormitory', 'home_address', 'grade_year',
            'major', 'department', 'minor_major', 'minor_department',  # ✅ 添加 minor_major
            'degree_level', 'credits_earned', 'minor_credits_earned'
        ]
        widgets = {
            'student_id_num': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'id_card': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'dormitory': forms.TextInput(attrs={'class': 'form-control'}),
            'home_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'grade_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'major': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'minor_major': forms.Select(attrs={'class': 'form-select'}),  # ✅ 新增
            'minor_department': forms.Select(attrs={'class': 'form-select'}),
            'degree_level': forms.TextInput(attrs={'class': 'form-control'}),
            'credits_earned': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'minor_credits_earned': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['minor_major'].required = False
        self.fields['minor_department'].required = False
        
        
        self.fields['minor_major'].empty_label = "请选择辅修专业（可选）"
        self.fields['minor_department'].empty_label = "请选择辅修院系（可选）"