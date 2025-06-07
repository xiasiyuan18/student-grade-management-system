# student_grade_management_system/users/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm

class CustomAuthenticationForm(AuthenticationForm):
    """
    继承Django内置的认证表单，并为其字段添加Bootstrap样式。
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 为用户名和密码字段添加 Bootstrap 的 form-control 类
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': '请输入用户名'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': '请输入密码'})