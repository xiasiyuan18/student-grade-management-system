# grades/serializers.py
from rest_framework import serializers

from courses.models import Course, TeachingAssignment  # 用于嵌套或ID表示
from users.models import Student  # 用于嵌套或ID表示

from .models import Grade


# 为了在GradeSerializer中显示更友好的信息，可以创建简单的嵌套序列化器
class SimpleStudentSerializer(serializers.ModelSerializer):
    student_id_num = serializers.CharField(
        source="student.student_id_num"
    )  # 假设Student模型有student_id_num
    name = serializers.CharField(source="student.name")  # 假设Student模型有name
    full_name = serializers.SerializerMethodField()  # 或者直接使用Student模型的__str__

    class Meta:
        model = Student
        fields = [
            "user_id",
            "name",
            "student_id_num",
        ]  # user_id 是 Student Profile 的主键 (user_id)

    def get_full_name(self, obj):
        return obj.name or obj.user.username


class SimpleCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["course_id", "course_name", "credits"]


class SimpleTeacherSerializer(serializers.ModelSerializer):
    # name = serializers.CharField(source='teacher.name') # 假设Teacher模型有name
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Student  # TODO: This should likely be Teacher, assuming a Teacher model exists in users.models
        fields = [
            "user_id",
            "name",
            "teacher_id_num",
        ]  # user_id 是 Teacher Profile 的主键 (user_id)

    def get_full_name(self, obj):
        return obj.name or obj.user.username


class SimpleTeachingAssignmentSerializer(serializers.ModelSerializer):
    course = SimpleCourseSerializer(read_only=True)
    teacher = SimpleTeacherSerializer(read_only=True)
    # semester = serializers.CharField() # 已有

    class Meta:
        model = TeachingAssignment
        fields = ["id", "course", "teacher", "semester"]


class GradeSerializer(serializers.ModelSerializer):
    student = SimpleStudentSerializer(read_only=True)  # 用于读取时显示学生信息
    student_id = serializers.IntegerField(
        write_only=True, help_text="要录入成绩的学生的ID (Student Profile PK)"
    )  # 写入时用ID

    teaching_assignment = SimpleTeachingAssignmentSerializer(
        read_only=True
    )  # 读取时显示授课安排信息
    teaching_assignment_id = serializers.IntegerField(
        write_only=True, help_text="授课安排的ID (TeachingAssignment PK)"
    )  # 写入时用ID

    score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="分数 (0.00-100.00)，可为空",
    )

    last_modified_by_username = serializers.CharField(
        source="last_modified_by.username", read_only=True, allow_null=True
    )

    # 从 teaching_assignment 中获取课程名称、教师名称、学期，用于只读显示
    course_name = serializers.CharField(
        source="teaching_assignment.course.course_name", read_only=True
    )
    teacher_name = serializers.CharField(
        source="teaching_assignment.teacher.name", read_only=True
    )  # 假设Teacher有name字段
    term = serializers.CharField(source="teaching_assignment.semester", read_only=True)

    class Meta:
        model = Grade
        fields = [
            "id",
            "student",  # 只读嵌套对象
            "student_id",  # 只写ID
            "teaching_assignment",  # 只读嵌套对象
            "teaching_assignment_id",  # 只写ID
            "course_name",  # 只读，方便前端显示
            "teacher_name",  # 只读
            "term",  # 只读
            "score",
            "entry_time",
            "last_modified_by_username",
            "last_modified_time",
        ]
        read_only_fields = (
            "id",
            "entry_time",
            "last_modified_time",
            "last_modified_by_username",
        )

    def create(self, validated_data):
        # DRF的ModelSerializer默认的create不适用于我们这种需要调用service层复杂逻辑的场景
        # 我们将在View中直接调用service函数
        raise NotImplementedError("请在View中调用service层进行创建。")

    def update(self, instance, validated_data):
        # 同样，更新也通过service层处理
        raise NotImplementedError("请在View中调用service层进行更新。")


class GradeUpdateSerializer(serializers.Serializer):  # 用于教师更新/录入成绩的输入
    student_id = serializers.IntegerField(
        required=True, help_text="学生ID (Student Profile PK)"
    )
    # teaching_assignment_id 已经在URL中，或者教师选择的上下文中
    score = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=6,
        help_text="分数 (例如 '85.5' 或空表示清除)",
    )

    def validate_score(self, value):
        from decimal import (Decimal,  # Import Decimal and InvalidOperation
                             InvalidOperation)

        if value is None or value.strip() == "":
            return None  # 允许清空分数
        try:
            score_decimal = Decimal(value)
            if not (Decimal("0.00") <= score_decimal <= Decimal("100.00")):
                raise serializers.ValidationError("分数必须在 0.00 到 100.00 之间。")
            return value  # 返回原始字符串，让service层再次处理Decimal转换，或直接返回Decimal
        except InvalidOperation:
            raise serializers.ValidationError("无效的分数格式，请输入数字。")
