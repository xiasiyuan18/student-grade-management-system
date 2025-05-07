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