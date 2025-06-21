from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group  
from rest_framework import serializers


from departments.models import Department, Major

from .models import (Student,  
                     Teacher)

CustomUser = get_user_model() 


class CustomUserSerializer(serializers.ModelSerializer):
    """
    用于 CustomUser 模型的序列化器
    """

    password = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"}
    )

    role = serializers.ChoiceField(choices=CustomUser.Role.choices, required=False)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "password",
            "is_active",
            "is_staff",
            "is_superuser",
            "last_login",
            "date_joined",
        ]
        read_only_fields = (
            "id",
            "last_login",
            "date_joined",
            "is_staff",
            "is_superuser",
        )
        extra_kwargs = {
            "password": {
                "write_only": True,
                "required": False,
            },  
           
        }

    def create(self, validated_data):
        role = validated_data.pop("role", CustomUser.Role.STUDENT)  
        user = CustomUser.objects.create_user(
            username=validated_data.pop("username"),
            email=validated_data.pop("email", None),
            password=validated_data.pop("password", None), 
            role=role,
            **validated_data  
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)


class StudentProfileSerializer(serializers.ModelSerializer):
    """
    用于 Student Profile 模型的序列化器
    在创建 Profile 时，通常也会创建或关联一个 CustomUser
    """


    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    user_role = serializers.CharField(
        source="user.role", read_only=True
    )  
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source="user",
        write_only=True,
        required=False, 
        allow_null=True,  
    )


    major = serializers.PrimaryKeyRelatedField(
        queryset=Major.objects.all(), allow_null=True, required=False
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        allow_null=True,
        required=False,
    )  
    minor_department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), allow_null=True, required=False
    )

   
    major_name = serializers.CharField(
        source="major.major_name", read_only=True, allow_null=True
    )
    department_name = serializers.CharField(
        source="department.dept_name", read_only=True, allow_null=True
    )

    class Meta:
        model = Student
        fields = [
            "user",  
            "username",
            "email",
            "user_role",  
            "user_id",  
            "student_id_num",
            "name",
            "id_card",
            "gender",
            "birth_date",
            "phone",
            "dormitory",
            "home_address",
            "grade_year",
            "major",
            "department",
            "minor_department", 
            "major_name",
            "department_name",  
            "degree_level",
            "credits_earned",
        ]
        read_only_fields = (
            "user",
            "username",
            "email",
            "user_role",
            "major_name",
            "department_name",
        )
    


class TeacherProfileSerializer(serializers.ModelSerializer):
    """
    用于 Teacher Profile 模型的序列化器
    """

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source="user",
        write_only=True,
        required=False,
        allow_null=True,
    )

    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    department_name = serializers.CharField(
        source="department.dept_name", read_only=True
    )

    class Meta:
        model = Teacher
        fields = [
            "user",
            "username",
            "email",
            "user_role",
            "user_id",
            "teacher_id_num",
            "name",
            "department",
            "department_name",
        ]
        read_only_fields = ("user", "username", "email", "user_role", "department_name")




from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _

CustomUser = get_user_model() 

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField( 
        label=_("用户名"),  
        write_only=True,
        required=True,
    )
    password = serializers.CharField(
        label=_("密码"),
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
        required=True,
    )

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        request = self.context.get("request")

        if not username or not password:
            # 这个检查其实可以由 required=True 处理，但多一层保险
            raise serializers.ValidationError(
                _("必须提供用户名和密码。"), code="authorization"
            )

        user = authenticate(request=request, username=username, password=password)

        if not user:
            # 用户名或密码错误
            raise serializers.ValidationError(
                _("用户名或密码有误。"), code="authorization"
            )

        if not user.is_active:
            # 用户账户被禁用
            raise serializers.ValidationError(
                _("用户账户已被禁用。"), code="authorization"
            )

        # 认证成功，将 user 对象附加到 attrs 中，方便视图使用
        attrs["user"] = user
        return attrs





class UserSelfUpdateSerializer(serializers.ModelSerializer):
    """用户更新自己非敏感基础信息的序列化器 (CustomUser)"""
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email'] # 用户可以修改这些
        # username (登录ID) 通常不允许修改
        # role, is_active, is_staff, is_superuser 绝对不能由用户自己修改

class StudentProfileSelfUpdateSerializer(serializers.ModelSerializer):
    """学生更新自己档案非身份相关信息的序列化器"""


    class Meta:
        model = Student
        # 列出学生可以自己修改的字段
        fields = ['name', 'id_card', 'gender', 'birth_date', 'phone', 'dormitory', 'home_address']
      


class TeacherProfileSelfUpdateSerializer(serializers.ModelSerializer):
    """教师更新自己档案非身份相关信息的序列化器"""
    # user = UserSelfUpdateSerializer(partial=True, required=False)

    class Meta:
        model = Teacher
        # 列出教师可以自己修改的字段
        fields = ['name']
        # teacher_id_num, department, title 通常由管理员管理
