# student_grade_management_system/grades/forms.py

from django import forms
from .models import Grade
from courses.models import TeachingAssignment, CourseEnrollment # 导入 CourseEnrollment
from users.models import Student
from django.db.models import Q # 用于复杂查询


# =============================================================================
# ✨ 新增: 专为管理员设计的表单 (用于管理员修改成绩功能)
# =============================================================================
class GradeFormForAdmin(forms.ModelForm):
    """
    专为管理员设计的成绩修改表单。
    允许管理员直接修改分数。
    这个表单被 AdminGradeUpdateView 使用。
    """
    class Meta:
        model = Grade
        # 只允许修改 'score' 字段
        fields = ['score'] 
        widgets = {
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'score': '分数 (0-100)',
        }
        help_texts = {
            'score': '请输入一个 0 到 100 之间的数值。绩点(GPA)将自动计算。'
        }


# =============================================================================
# 您原有的表单 (已保留并优化)
# =============================================================================

class GradeEntryForm(forms.ModelForm):
    """
    您原有的表单，用于单个成绩的创建。
    （注：当前教师端的成绩录入视图未使用此表单，而是直接处理POST请求，但此表单已保留备用）
    """
    class Meta:
        model = Grade
        fields = ['student', 'teaching_assignment', 'score']
        widgets = {
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

    def clean(self):
        """
        验证学生是否确实选修了该门课程。
        """
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        teaching_assignment = cleaned_data.get('teaching_assignment')

        if student and teaching_assignment:
            # 检查 CourseEnrollment 中是否存在对应的选课记录
            is_enrolled = CourseEnrollment.objects.filter(
                student=student,
                teaching_assignment=teaching_assignment,
                status='ENROLLED' # 确保是“已选课”状态
            ).exists()
            
            if not is_enrolled:
                raise forms.ValidationError(f"验证失败：学生 {student.name} 并未选修课程《{teaching_assignment.course.course_name}》。")

        return cleaned_data


class SelectTeachingAssignmentForm(forms.Form):
    """
    您原有的表单，用于让教师选择一个授课安排。
    """
    teaching_assignment = forms.ModelChoiceField(
        queryset=TeachingAssignment.objects.all(),
        label="选择授课安排",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="--- 请选择您教授的课程 ---" # 增加友好提示
    )

    def __init__(self, *args, **kwargs):
        request_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if request_user and request_user.is_authenticated:
            try:
                # 只有教师能选择自己的授课安排
                teacher_profile = request_user.teacher_profile
                self.fields['teaching_assignment'].queryset = TeachingAssignment.objects.filter(
                    teacher=teacher_profile
                ).select_related('course').order_by('-semester', 'course__course_name')
            except CustomUser.teacher_profile.RelatedObjectDoesNotExist:
                # 如果用户不是教师，则 queryset 为空
                self.fields['teaching_assignment'].queryset = TeachingAssignment.objects.none()
        else:
            self.fields['teaching_assignment'].queryset = TeachingAssignment.objects.none()