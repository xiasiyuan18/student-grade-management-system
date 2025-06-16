# users/forms.py

from django import forms
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from .models import Student, Teacher
from departments.models import Major, Department

User = get_user_model()


class CustomAuthenticationForm(AuthenticationForm):
    """
    用于登录的自定义认证表单。
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': '请输入用户名'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': '请输入密码'})


# =============================================================================
# 管理员创建功能表单
# =============================================================================
class StudentCreateForm(forms.Form):
    """
    管理员创建新学生的表单。
    """
    username = forms.CharField(label="登录用户名", max_length=150, help_text="学生的唯一登录账号。")
    password = forms.CharField(label="初始密码", widget=forms.PasswordInput, help_text="请为学生设置一个安全的初始密码。")
    name = forms.CharField(label="姓名", max_length=100, help_text="学生的真实姓名。")
    student_id_num = forms.CharField(label="学号", max_length=50)
    id_card = forms.CharField(label="身份证号", max_length=18)
    gender = forms.ChoiceField(label="性别", choices=Student.GENDER_CHOICES, widget=forms.Select)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), label="所属院系")
    major = forms.ModelChoiceField(queryset=Major.objects.all(), label="所属专业")
    birth_date = forms.DateField(label="出生日期", required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    phone = forms.CharField(label="联系电话", required=False, max_length=50)
    grade_year = forms.IntegerField(label="入学年份", required=False)
    degree_level = forms.CharField(label="学位等级", required=False, max_length=20)
    dormitory = forms.CharField(label="宿舍信息", required=False, max_length=100)
    home_address = forms.CharField(label="家庭地址", required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("此用户名已被占用，请选择其他用户名。")
        return username
        
    def clean_student_id_num(self):
        student_id_num = self.cleaned_data.get('student_id_num')
        if Student.objects.filter(student_id_num=student_id_num).exists():
            raise forms.ValidationError("此学号已被占用，请核对后输入。")
        return student_id_num

    @transaction.atomic
    def save(self):
        cleaned_data = self.cleaned_data
        user = User.objects.create_user(
            username=cleaned_data['username'],
            password=cleaned_data['password'],
            first_name=cleaned_data['name'][:30],
            role="STUDENT"
        )
        # 移除 cleaned_data 中不属于 Student 模型的字段
        student_data = {k: v for k, v in cleaned_data.items() if hasattr(Student, k)}
        Student.objects.create(user=user, **student_data)
        return user


class TeacherCreateForm(forms.Form):
    """
    管理员创建新教师的表单。
    """
    username = forms.CharField(label="登录用户名", max_length=150)
    password = forms.CharField(label="初始密码", widget=forms.PasswordInput)
    name = forms.CharField(label="教师姓名", max_length=100)
    teacher_id_num = forms.CharField(label="教师工号", max_length=50)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), label="所属院系", empty_label="请选择院系")
    email = forms.EmailField(label="邮箱地址", required=False)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("此用户名已被占用。")
        return username

    def clean_teacher_id_num(self):
        teacher_id_num = self.cleaned_data.get('teacher_id_num')
        if Teacher.objects.filter(teacher_id_num=teacher_id_num).exists():
            raise forms.ValidationError("此工号已被占用。")
        return teacher_id_num

    @transaction.atomic
    def save(self):
        cleaned_data = self.cleaned_data
        user = User.objects.create_user(
            username=cleaned_data['username'],
            password=cleaned_data['password'],
            first_name=cleaned_data['name'],
            email=cleaned_data.get('email', ''),
            role=User.Role.TEACHER
        )
        Teacher.objects.create(
            user=user,
            teacher_id_num=cleaned_data['teacher_id_num'],
            name=cleaned_data['name'],
            department=cleaned_data['department']
        )
        return user


# =============================================================================
# 管理员更新功能表单
# =============================================================================
class TeacherUpdateForm(forms.ModelForm):
    username = forms.CharField(label="登录用户名")
    email = forms.EmailField(label="邮箱地址", required=False)

    class Meta:
        model = Teacher
        fields = ['name', 'teacher_id_num', 'department']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
        self.order_fields = ['username', 'email', 'name', 'teacher_id_num', 'department']

    @transaction.atomic
    def save(self, commit=True):
        teacher = super().save(commit=False)
        user = teacher.user
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['name']
        if commit:
            teacher.save()
            user.save()
        return teacher

class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']

class StudentProfileEditForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = ['user']


# =============================================================================
# 用户个人中心更新表单
# =============================================================================
class StudentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['phone', 'dormitory', 'home_address']

class TeacherProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'student_id_num', 'name', 'id_card', 'gender', 'birth_date',
            'phone', 'dormitory', 'home_address', 'grade_year',
            'major', 'department', 'minor_major', 'minor_department',
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
            'minor_major': forms.Select(attrs={'class': 'form-select'}),
            'minor_department': forms.Select(attrs={'class': 'form-select'}),
            'degree_level': forms.TextInput(attrs={'class': 'form-control'}),
            'credits_earned': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'minor_credits_earned': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置辅修字段为非必填
        self.fields['minor_major'].required = False
        self.fields['minor_department'].required = False