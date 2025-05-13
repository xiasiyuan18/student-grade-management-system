from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group  # 如果需要在序列化器中处理用户组
from rest_framework import serializers

# 假设 Department 和 Major 模型在 departments app 中
from departments.models import Department, Major

from .models import (Student,  # 导入你的 Student Profile 和 Teacher Profile 模型
                     Teacher)

CustomUser = get_user_model()  # 获取 settings.AUTH_USER_MODEL 指向的模型


class CustomUserSerializer(serializers.ModelSerializer):
    """
    用于 CustomUser 模型的序列化器
    """

    # 对于密码字段，通常只在创建或更新时写入，不用于读取
    password = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"}
    )
    # role 字段是 CustomUser 上的，可以读写（但创建时可能由特定逻辑设置）
    # choices 可以从模型中获取
    role = serializers.ChoiceField(choices=CustomUser.Role.choices, required=False)
    # groups = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True, required=False) # 可选：管理用户组

    class Meta:
        model = CustomUser
        # AbstractUser 包含: username, first_name, last_name, email, password (已处理)
        # groups, user_permissions (ManyToManyField，处理方式可以更复杂或单独API)
        # is_staff, is_active, is_superuser, last_login, date_joined
        # 加上我们自定义的 role
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
            # 'groups', 'user_permissions' # 通常不直接通过用户序列化器批量修改，而是通过专门接口或Admin
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
            },  # 创建时如果通过 create_user 则密码是必需的
            # 更新时密码是可选的
        }

    def create(self, validated_data):
        # 使用 CustomUser 的 Manager 来创建用户，确保密码被正确哈希
        # role 应该在 validated_data 中，或者在此处设置默认值
        role = validated_data.pop("role", CustomUser.Role.STUDENT)  # 示例默认值
        user = CustomUser.objects.create_user(
            username=validated_data.pop("username"),
            email=validated_data.pop("email", None),
            password=validated_data.pop("password", None),  # create_user 会处理 None
            role=role,
            **validated_data  # 其他 AbstractUser 的字段如 first_name, last_name
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        # 更新其他字段
        return super().update(instance, validated_data)


class StudentProfileSerializer(serializers.ModelSerializer):
    """
    用于 Student Profile 模型的序列化器
    在创建 Profile 时，通常也会创建或关联一个 CustomUser
    """

    # 用于读取 CustomUser 的信息
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    user_role = serializers.CharField(
        source="user.role", read_only=True
    )  # 显示关联用户的角色

    # 用于创建关联的 CustomUser (如果 Profile 创建和 User 创建是绑定的)
    # 如果是先创建 User 再创建 Profile，这里的逻辑会不同
    # 这里假设通过 Profile API 创建时，也一并处理 User 的核心信息
    # 如果希望通过此序列化器创建 User，需要在 create 方法中特殊处理
    # 或者假设 User 已经存在，只传递 user_id 来关联
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source="user",
        write_only=True,
        required=False,  # 如果是更新已存在的Profile，或者创建时会单独创建User则为False
        allow_null=True,  # 如果允许 Profile 不关联 User (通常不允许)
    )

    # Student Profile 特有的字段
    # 外键使用 PrimaryKeyRelatedField 以便通过 ID 进行关联
    major = serializers.PrimaryKeyRelatedField(
        queryset=Major.objects.all(), allow_null=True, required=False
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        allow_null=True,
        required=False,
        source="department",
    )  # 明确 source
    minor_department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), allow_null=True, required=False
    )

    # 如果希望在 API 响应中也包含关联对象的名称等详细信息，可以使用嵌套序列化器或 StringRelatedField
    major_name = serializers.CharField(
        source="major.major_name", read_only=True, allow_null=True
    )
    department_name = serializers.CharField(
        source="department.dept_name", read_only=True, allow_null=True
    )

    class Meta:
        model = Student
        fields = [
            "user",  # 这是 OneToOneField 到 CustomUser，读取时会是 CustomUser 的 PK
            "username",
            "email",
            "user_role",  # 从关联的 CustomUser 读取
            "user_id",  # 用于写入时关联 CustomUser ID
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
            "minor_department",  # 用于写入外键
            "major_name",
            "department_name",  # 用于读取外键名称
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
        # student_id_num 通常也应该是创建后不可更改或有特定验证逻辑

    # create 和 update 方法可能需要更复杂的逻辑来处理 User 和 Profile 的同步创建/更新
    # 例如，创建 Student Profile 时，如果 user_id 未提供，可能需要先创建一个 CustomUser
    # 这里简化处理，假设 User 的创建/关联逻辑在视图层或更上层处理，或者此 Serializer 主要用于已关联 User 的 Profile 管理


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

    # 同样，create 和 update 方法可能需要处理 User 和 Profile 的关联


from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _

CustomUser = get_user_model()  # 获取在 settings.py 中定义的 AUTH_USER_MODEL


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(  # AbstractUser 默认的登录字段是 username
        label=_("用户名"),  # 前端对应的可能是学号、工号或管理员设置的用户名
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

        # 使用 Django 的 authenticate 函数进行认证
        # 它会使用 settings.AUTHENTICATION_BACKENDS 中的后端
        # 默认的 ModelBackend 会基于 AUTH_USER_MODEL (CustomUser) 和其 USERNAME_FIELD (username) 进行验证
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
