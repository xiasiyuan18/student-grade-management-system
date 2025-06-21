from rest_framework import serializers

from courses.models import Course, TeachingAssignment  
from users.models import Student, Teacher   

from .models import Grade


class SimpleStudentSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "user_id",
            "name",
            "student_id_num",
            "full_name",
        ]

    def get_full_name(self, obj):
        return obj.name or obj.user.username


class SimpleCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["course_id", "course_name", "credits"]


class SimpleTeacherSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = [
            "user_id",
            "name",
            "teacher_id_num",
            "full_name",
        ]

    def get_full_name(self, obj):
        return obj.name or obj.user.username


class SimpleTeachingAssignmentSerializer(serializers.ModelSerializer):
    course = SimpleCourseSerializer(read_only=True)
    teacher = SimpleTeacherSerializer(read_only=True)

    class Meta:
        model = TeachingAssignment
        fields = ["id", "course", "teacher", "semester"]


class GradeSerializer(serializers.ModelSerializer):
    student = SimpleStudentSerializer(read_only=True)
    student_id = serializers.IntegerField(
        write_only=True, help_text="要录入成绩的学生的ID (Student Profile PK)"
    )

    teaching_assignment = SimpleTeachingAssignmentSerializer(read_only=True)
    teaching_assignment_id = serializers.IntegerField(
        write_only=True, help_text="授课安排的ID (TeachingAssignment PK)"
    )

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

    course_name = serializers.CharField(
        source="teaching_assignment.course.course_name", read_only=True
    )
    teacher_name = serializers.CharField(
        source="teaching_assignment.teacher.name", read_only=True
    )
    term = serializers.CharField(source="teaching_assignment.semester", read_only=True)

    class Meta:
        model = Grade
        fields = [
            "id",
            "student",
            "student_id",
            "teaching_assignment",
            "teaching_assignment_id",
            "course_name",
            "teacher_name",
            "term",
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
        raise NotImplementedError("请在View中调用service层进行创建。")

    def update(self, instance, validated_data):
        raise NotImplementedError("请在View中调用service层进行更新。")


class GradeUpdateSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(
        required=True, help_text="学生ID (Student Profile PK)"
    )
    score = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=6,
        help_text="分数 (例如 '85.5' 或空表示清除)",
    )

    def validate_score(self, value):
        from decimal import (Decimal, InvalidOperation)

        if value is None or value.strip() == "":
            return None
        try:
            score_decimal = Decimal(value)
            if not (Decimal("0.00") <= score_decimal <= Decimal("100.00")):
                raise serializers.ValidationError("分数必须在 0.00 到 100.00 之间。")
            return value
        except InvalidOperation:
            raise serializers.ValidationError("无效的分数格式，请输入数字。")
