# users/forms.py (解决冲突后的最终版本)

from django import forms
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm # 解决方案：保留队友的 import
from .models import Student
from departments.models import Major, Department

User = get_user_model()


# --- 解决方案：保留队友的登录表单 ---
class CustomAuthenticationForm(AuthenticationForm):
    """
    继承Django内置的认证表单，并为其字段添加Bootstrap样式。
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 为用户名和密码字段添加 Bootstrap 的 form-control 类
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': '请输入用户名'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': '请输入密码'})


# --- 解决方案：保留您的所有教师和学生管理表单 ---

# --- 教师账户创建表单 ---
class TeacherForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="初始密码")
    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name')
        labels = {
            'username': '登录用户名',
            'email': '邮箱地址',
            'first_name': '名',
            'last_name': '姓',
        }

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = User.Role.TEACHER # 设定角色为教师
        if commit:
            user.save()
        return user

# --- 最终的学生创建表单 ---
class StudentForm(forms.Form):
    username = forms.CharField(label="登录用户名", max_length=150, help_text="学生的登录账号。", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="初始密码")
    email = forms.EmailField(label="邮箱地址", required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    name = forms.CharField(label="姓名", max_length=100, help_text="学生的真实姓名。", widget=forms.TextInput(attrs={'class': 'form-control'}))
    student_id_num = forms.CharField(label="学号", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    id_card = forms.CharField(label="身份证号", max_length=18, widget=forms.TextInput(attrs={'class': 'form-control'}))
    gender = forms.ChoiceField(label="性别", choices=Student.GENDER_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(), label="所属院系", widget=forms.Select(attrs={'class': 'form-select'}))
    major = forms.ModelChoiceField(queryset=Major.objects.all(), label="所属专业", widget=forms.Select(attrs={'class': 'form-select'}))
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("此用户名已被占用，请选择其他用户名。")
        return username

    @transaction.atomic
    def save(self):
        cleaned_data = self.cleaned_data
        
        # 创建 CustomUser 账户
        user = User.objects.create_user(
            username=cleaned_data['username'],
            password=cleaned_data['password'],
            first_name=cleaned_data['name'][:30],
            email=cleaned_data.get('email', ''),
            role="STUDENT"
        )

        # 创建 Student 档案
        student_profile = Student.objects.create(
            user=user,
            student_id_num=cleaned_data['student_id_num'],
            name=cleaned_data['name'],
            id_card=cleaned_data['id_card'],
            gender=cleaned_data['gender'],
            major=cleaned_data['major'],
            department=cleaned_data['department']
        )
        return user


# 学生个人档案更新表单
class StudentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('phone', 'dormitory', 'home_address') 
        labels = {
            'phone': '我的联系电话',
            'dormitory': '我的宿舍信息',
            'home_address': '我的家庭地址',
        }
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'dormitory': forms.TextInput(attrs={'class': 'form-control'}),
            'home_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# 专为教师修改个人信息设计的表单
class TeacherProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
        labels = {
            'email': '邮箱地址',
            'first_name': '名',
            'last_name': '姓',
        }
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }