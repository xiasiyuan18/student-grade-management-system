from django import forms
from .models import Grade
from courses.models import TeachingAssignment, CourseEnrollment 
from users.models import Student
from django.db.models import Q


class GradeFormForAdmin(forms.ModelForm):
    class Meta:
        model = Grade
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


class GradeEntryForm(forms.ModelForm):
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
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        teaching_assignment = cleaned_data.get('teaching_assignment')

        if student and teaching_assignment:
            # 检查选课记录
            is_enrolled = CourseEnrollment.objects.filter(
                student=student,
                teaching_assignment=teaching_assignment,
                status='ENROLLED'
            ).exists()
            
            if not is_enrolled:
                raise forms.ValidationError(f"验证失败：学生 {student.name} 并未选修课程《{teaching_assignment.course.course_name}》。")

        return cleaned_data


class SelectTeachingAssignmentForm(forms.Form):
    teaching_assignment = forms.ModelChoiceField(
        queryset=TeachingAssignment.objects.all(),
        label="选择授课安排",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="--- 请选择您教授的课程 ---"
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
            except request_user.teacher_profile.RelatedObjectDoesNotExist:
                self.fields['teaching_assignment'].queryset = TeachingAssignment.objects.none()
        else:
            self.fields['teaching_assignment'].queryset = TeachingAssignment.objects.none()