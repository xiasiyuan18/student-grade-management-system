from django import forms
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Student
from departments.models import Major, Department

User = get_user_model()

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
            # 注意：密码字段的 widget 在上面单独定义了，这里的不生效，但写上保持统一性
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
    # (所有字段定义保持不变)
    username = forms.CharField(label="登录用户名", max_length=150, help_text="学生的登录账号。", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="初始密码")
    email = forms.EmailField(label="邮箱地址", required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    name = forms.CharField(label="姓名", max_length=100, help_text="学生的真实姓名。", widget=forms.TextInput(attrs={'class': 'form-control'}))
    student_id_num = forms.CharField(label="学号", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    id_card = forms.CharField(label="身份证号", max_length=18, widget=forms.TextInput(attrs={'class': 'form-control'}))
    gender = forms.ChoiceField(label="性别", choices=Student.GENDER_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(), label="所属院系", widget=forms.Select(attrs={'class': 'form-select'}))
    major = forms.ModelChoiceField(queryset=Major.objects.all(), label="所属专业", widget=forms.Select(attrs={'class': 'form-select'}))
    
    # ✨ 关键修正：添加一个自定义的验证方法 ✨
    def clean_username(self):
        # 获取用户在表单中输入的用户名
        username = self.cleaned_data.get('username')
        # 检查数据库中是否已存在同名用户
        if User.objects.filter(username=username).exists():
            # 如果存在，就引发一个验证错误，这个错误信息会显示在前端页面上
            raise forms.ValidationError("此用户名已被占用，请选择其他用户名。")
        # 如果不存在，就返回这个用户名，验证通过
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
        model = Student # 这个表单的模型是 Student
        
        # ✨ 核心修正：只包含 Student 模型中实际存在且适合学生修改的字段
        fields = ('phone', 'dormitory', 'home_address') 
        
        # 为表单字段设置更友好的中文标签
        labels = {
            'phone': '我的联系电话',
            'dormitory': '我的宿舍信息',
            'home_address': '我的家庭地址',
        }

        # 为输入框添加 Bootstrap 样式，并为地址使用大一点的文本框
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'dormitory': forms.TextInput(attrs={'class': 'form-control'}),
            'home_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ✨ 新增：专为教师修改个人信息设计的表单
class TeacherProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        # 重要的安全措施：只允许教师修改这几个字段
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