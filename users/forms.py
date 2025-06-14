# users/forms.py (解决冲突后的最终版本)

from django import forms
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from .models import Student, Teacher  # 确保导入了 Teacher 模型
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
    
    # 添加教师档案相关字段
    teacher_id_num = forms.CharField(
        label="教师工号", 
        max_length=50, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    name = forms.CharField(
        label="教师姓名", 
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(), 
        label="所属院系", 
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="请选择院系"
    )
    
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
        }

    def clean_teacher_id_num(self):
        teacher_id_num = self.cleaned_data.get('teacher_id_num')
        if teacher_id_num and Teacher.objects.filter(teacher_id_num=teacher_id_num).exists():
            raise forms.ValidationError("此工号已被占用，请选择其他工号。")
        return teacher_id_num

    def save(self, commit=True):
        """只保存用户，教师档案由视图处理"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = User.Role.TEACHER
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


# 学生个人档案更新表单（学生自己使用）
class StudentProfileUpdateForm(forms.ModelForm):
    """学生修改自己个人信息的表单"""
    class Meta:
        model = Student
        # 学生只能修改这些非敏感信息
        fields = ['phone', 'dormitory', 'home_address'] 
        labels = {
            'phone': '联系电话',
            'dormitory': '宿舍信息',
            'home_address': '家庭地址',
        }
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '请输入您的联系电话'
            }),
            'dormitory': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '如：1号楼201室'
            }),
            'home_address': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': '请输入您的家庭详细地址'
            }),
        }
        help_texts = {
            'phone': '用于紧急联系和通知',
            'dormitory': '您的宿舍房间号',
            'home_address': '您的家庭详细住址',
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

class StudentUpdateForm(forms.ModelForm):
    """管理员更新学生基本账户信息的表单"""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
        labels = {
            'username': '登录用户名',
            'email': '邮箱地址',
            'first_name': '名',
            'last_name': '姓',
            'is_active': '账户激活状态',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class StudentProfileEditForm(forms.ModelForm):
    """管理员编辑学生档案信息的表单"""
    class Meta:
        model = Student
        fields = [
            'name', 'student_id_num', 'id_card', 'gender', 'birth_date',
            'phone', 'dormitory', 'home_address', 'grade_year',
            'major', 'department', 'minor_department', 'degree_level', 'credits_earned'
        ]
        labels = {
            'name': '学生姓名',
            'student_id_num': '学号',
            'id_card': '身份证号',
            'gender': '性别',
            'birth_date': '出生日期',
            'phone': '联系电话',
            'dormitory': '宿舍信息',
            'home_address': '家庭地址',
            'grade_year': '入学年份',
            'major': '专业',
            'department': '所属院系',
            'minor_department': '辅修院系',
            'degree_level': '学位等级',
            'credits_earned': '已修学分',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'student_id_num': forms.TextInput(attrs={'class': 'form-control'}),
            'id_card': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'dormitory': forms.TextInput(attrs={'class': 'form-control'}),
            'home_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'grade_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'major': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'minor_department': forms.Select(attrs={'class': 'form-select'}),
            'degree_level': forms.TextInput(attrs={'class': 'form-control'}),
            'credits_earned': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }