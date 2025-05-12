from rest_framework import serializers
from .models import Student # 你的 Student 模型

class StudentSerializer(serializers.ModelSerializer):
    # 为了创建用户时能设置密码，但读取时不显示密码原文
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = Student
        # 列出你希望通过 API 暴露的字段
        # 对于 Student (AUTH_USER_MODEL)，要小心处理密码等敏感信息
        fields = [
            'id', 'student_id', 'name', 'id_card', 'dormitory',
            'home_address', 'phone', 'birth_date', 'gender', 'grade',
            'major_id', 'department_id', 'minor_department_id',
            'degree_level', 'credits_earned', 'password', # password 是 write_only
            'is_active', 'is_staff', 'last_login', 'date_joined' # 基础用户字段
        ]
        read_only_fields = ('id', 'last_login', 'date_joined', 'is_staff') # 通常这些字段不应由 API直接修改

    def create(self, validated_data):
        # 使用 StudentManager 中的 create_user 方法来确保密码被正确哈希
        # 确保你的 StudentManager.create_user 接受这些参数
        password = validated_data.pop('password', None)
        # student_id 应该是 validated_data 中的一个键
        student = Student.objects.create_user(**validated_data, password=password)
        return student

    def update(self, instance, validated_data):
        # 更新时，如果提供了密码，则单独处理
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        # 调用父类的 update 方法来更新其他字段
        instance = super().update(instance, validated_data)
        instance.save()
        return instance
    

from rest_framework import serializers
from .models import Teacher # 导入您的 Teacher 模型
# from departments.serializers import DepartmentSerializer # 如果需要在教师信息中嵌套显示院系详情

class TeacherSerializer(serializers.ModelSerializer):
    # 为了创建或更新用户时能设置密码，但读取时不显示密码原文
    password = serializers.CharField(
        write_only=True,      # 只在写入（创建/更新）时使用
        required=False,       # 更新时不强制要求提供密码
        allow_blank=True,     # 允许在更新时传入空字符串（如果业务逻辑允许清空或不处理空密码）
        style={'input_type': 'password'}
    )

    # 如果你想在返回教师信息时，显示院系的名称而不是仅仅ID，可以这样做：
    # department_name = serializers.CharField(source='department.name', read_only=True)
    # 或者使用嵌套序列化器 (如果DepartmentSerializer已定义)
    # department = DepartmentSerializer(read_only=True)
    # 如果只需要 department_id 进行写操作，而读操作时用上面的嵌套或source，
    # 那么 department 字段（外键）本身可能需要特殊处理或在 fields 中分别指定。
    # 通常 ModelSerializer 会自动处理 ForeignKey 为 PrimaryKeyRelatedField。

    # 如果 department 字段在API层面希望接收的是院系ID，然后在序列化器中处理成对象
    # (但ModelSerializer默认会将ForeignKey字段处理为PrimaryKeyRelatedField，这通常是期望的行为，
    # 它期望接收ID，并能正确关联)

    class Meta:
        model = Teacher
        # 列出希望通过 API 暴露的字段
        fields = [
            'teacher_id',       # 主键，通常是 read_only (由模型定义 primary_key=True)
            'name',
            'department',       # 外键，默认会是院系的ID。创建/更新时传ID，读取时也是ID。
                                # 如果想在读取时显示更详细的院系信息，见上面的注释。
            'password',         # write_only，用于设置密码
            'is_active',
            'is_staff',
            # 'groups',         # 如果需要管理用户组
            # 'user_permissions',# 如果需要管理特定权限
            'last_login',       # 由Django自动管理
            'date_joined'       # 由Django自动管理或有默认值
        ]
        read_only_fields = (
            'teacher_id',       # 因为它是主键且通常不应被API修改 (除非有特定业务需求且管理员操作)
            'last_login',
            'date_joined'
        )
        # 'is_staff' 的修改权限通常也比较严格，可以考虑加入 read_only_fields，由管理员在Admin后台或特定API修改。

    def create(self, validated_data):
        """
        创建新的教师用户。
        """
        password = validated_data.pop('password', None)
        
        # ModelSerializer在处理ForeignKey时，如果validated_data['department']是ID,
        # 它通常会期望一个Department实例。
        # 但由于TeacherManager.create_user的实现，它也期望一个Department实例。
        # 如果前端直接传递 department_id，你可能需要在这里或Manager中进行转换。
        # 假设 validated_data['department'] 已经是 Department 实例 (DRF的PrimaryKeyRelatedField会处理ID到实例的转换，如果配置正确)
        # 或者 Manager 的 create_user 接受 department_id 并内部查找。
        # 为了与我们之前 TeacherManager 的定义匹配，这里假设 validated_data['department'] 是一个 Department 实例。
        # 如果前端传的是ID，你的视图或序列化器可能需要先获取Department对象。

        # 确保 REQUIRED_FIELDS (如 name, department) 存在于 validated_data 中
        # ModelSerializer 的验证阶段通常会处理 required=True 的字段
        
        teacher = Teacher.objects.create_user(**validated_data, password=password)
        return teacher

    def update(self, instance, validated_data):
        """
        更新已存在的教师用户信息。
        """
        password = validated_data.pop('password', None)

        # 更新其他字段
        # ModelSerializer的默认行为是迭代validated_data中的字段并设置到instance上
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password: # 如果请求中提供了新密码
            instance.set_password(password) # 安全地设置新密码

        instance.save() # 保存所有更改
        return instance
