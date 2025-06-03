# departments/forms.py
from django import forms
from .models import Department, Major

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = '__all__'
        # 为表单字段添加Bootstrap样式类
        widgets = {
            'dept_code': forms.TextInput(attrs={'class': 'form-control'}),
            'dept_name': forms.TextInput(attrs={'class': 'form-control'}),
            'office_location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class MajorForm(forms.ModelForm):
    class Meta:
        model = Major
        fields = '__all__'
        widgets = {
            'major_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'bachelor_credits_required': forms.NumberInput(attrs={'class': 'form-control'}),
            'master_credits_required': forms.NumberInput(attrs={'class': 'form-control'}),
            'doctor_credits_required': forms.NumberInput(attrs={'class': 'form-control'}),
        }