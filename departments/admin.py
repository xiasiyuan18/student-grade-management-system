from django.contrib import admin

# departments/admin.py

from .models import Department, Major

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('dept_code', 'dept_name', 'office_location', 'phone_number')
    search_fields = ('dept_code', 'dept_name')
    ordering = ['dept_code']

@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ('major_name', 'department', 'bachelor_credits_required', 'master_credits_required', 'doctor_credits_required')
    search_fields = ('major_name', 'department__dept_name') # 可以搜索关联院系的名称
    list_filter = ('department',) # 按所属院系筛选
    ordering = ['department', 'major_name']
