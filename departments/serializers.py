from rest_framework import serializers
from .models import Department, Major

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'dept_code', 'dept_name', 'office_location', 'phone_number']
        read_only_fields = ['id']

class MajorSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.dept_name', read_only=True, allow_null=True)

    class Meta:
        model = Major
        fields = [
            'id',
            'major_name',
            'department', # 序列化时是ID，反序列化时接收ID
            'department_name', # 只读，用于输出
            'bachelor_credits_required',
            'master_credits_required',
            'doctor_credits_required'
        ]
        read_only_fields = ['id', 'department_name']