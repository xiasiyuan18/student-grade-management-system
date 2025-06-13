# student_grade_management_system/grades/forms.py
from django import forms
from .models import Grade
from courses.models import TeachingAssignment
from users.models import Student
from django.db.models import Q # 用于复杂查询

class GradeEntryForm(forms.ModelForm):
    # 教师需要选择授课安排，然后才能为学生打分
    # 这个表单假设用于单个学生的成绩录入或修改
    # 如果是批量录入，需要 FormSet，我们先从单个开始

    class Meta:
        model = Grade
        fields = ['student', 'teaching_assignment', 'score']
        widgets = {
            # 学生和授课安排通常在前端通过某种选择机制预填充或只读显示
            # 或者在创建时通过URL参数传递
            'student': forms.Select(attrs={'class': 'form-select'}),
            'teaching_assignment': forms.Select(attrs={'class': 'form-select'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '请输入分数 (0-100)'}),
        }
        labels = {
            'student': '学生',
            'teaching_assignment': '授课安排',
            'score': '分数',
        }
        help_texts = {
            'score': '百分制分数，保留两位小数，范围0.00-100.00',
        }

    # 可以添加自定义的 clean 方法来验证业务逻辑，例如确保学生属于该授课安排
    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        teaching_assignment = cleaned_data.get('teaching_assignment')

        if student and teaching_assignment:
            # 假设 TeachingAssignment 包含与学生相关的班级信息
            # 或者，更直接地，确保这个学生确实应该在这门课的这个授课安排下被评分。
            # 这可能需要更复杂的逻辑，例如检查学生是否选修了这门课。
            # 为了简化，初期可以假设所有与 teaching_assignment 关联的学生都可以在这里被录入
            # 或者，如果 TeachingAssignment 有一个 related_name 到 students_enrolled，可以检查：
            # if not teaching_assignment.students_enrolled.filter(pk=student.pk).exists():
            #     raise forms.ValidationError("该学生不属于此授课安排。")
            pass # 暂时不添加复杂的验证

        return cleaned_data


# 教师选择授课安排的表单 (用于第一步)
class SelectTeachingAssignmentForm(forms.Form):
    teaching_assignment = forms.ModelChoiceField(
        queryset=TeachingAssignment.objects.all(), # 教师只能看到自己的授课安排，这需要在视图中过滤
        label="选择授课安排",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        request_user = kwargs.pop('user', None) # 从 kwargs 获取当前请求的用户
        super().__init__(*args, **kwargs)
        if request_user and request_user.is_authenticated:
            # 只有教师能选择自己的授课安排
            if hasattr(request_user, 'teacher_profile') and request_user.teacher_profile:
                self.fields['teaching_assignment'].queryset = TeachingAssignment.objects.filter(teacher=request_user.teacher_profile)
            else:
                self.fields['teaching_assignment'].queryset = TeachingAssignment.objects.none() # 非教师用户无权选择