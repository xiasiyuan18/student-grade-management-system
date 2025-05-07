from rest_framework import serializers
from .models import Grade # 你的 Grade 模型

class GradeSerializer(serializers.ModelSerializer):
    # 你可能希望在读取时显示关联对象的更友好表示，而不是ID
    # student_name = serializers.StringRelatedField(source='student.name', read_only=True)
    # course_name = serializers.StringRelatedField(source='course.name', read_only=True)
    # teacher_name = serializers.StringRelatedField(source='teacher.name', read_only=True)

    class Meta:
        model = Grade
        fields = '__all__'
        # 如果添加了上面的 StringRelatedField，也可以包含它们:
        # fields = [
        #     'id', 'student', 'course', 'teacher', 'term', 'score',
        #     'entry_time', 'last_modified_by', 'last_modified_time',
        #     'student_name', 'course_name', 'teacher_name' # 只读的友好名称
        # ]
        read_only_fields = ('entry_time', 'last_modified_time') # 这些通常是自动设置的

    # 你可以在这里添加验证逻辑，例如 score 的范围
    def validate_score(self, value):
        if value is not None and (value < 0 or value > 100): # 假设百分制
            raise serializers.ValidationError("分数必须在 0 到 100 之间。")
        return value