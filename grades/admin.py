# grades/admin.py
from django import forms
from django.contrib import admin
from .models import Grade

# 自定义 Grade 表单以添加验证
class GradeAdminForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = '__all__' # 或者列出所有你希望在表单中出现的字段

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score is not None: # 允许成绩为空（例如尚未录入）
            if score < 0 or score > 100: # 假设是百分制
                raise forms.ValidationError("分数必须在 0 到 100 之间。")
        return score

    # 你也可以添加 clean() 方法进行跨字段验证
    # def clean(self):
    #     cleaned_data = super().clean()
    #     # ... 你的跨字段验证逻辑 ...
    #     return cleaned_data

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    form = GradeAdminForm # 使用自定义表单
    list_display = ('student_name_display', 'course_name_display', 'teacher_name_display', 'term', 'score', 'entry_time', 'last_modified_by')
    list_filter = ('term', 'course', 'teacher') # 按学期、课程、教师筛选
    search_fields = ('student__student_id', 'student__name', 'course__name', 'course__course_id_num', 'teacher__name', 'teacher__teacher_id_num') # 搜索学生、课程、教师信息
    ordering = ('-entry_time', 'student') # 默认按录入时间降序，然后按学生排序

    # 对于外键字段，使用 raw_id_fields 或 autocomplete_fields 可以提高性能和易用性
    # 特别是当关联的模型实例很多时
    raw_id_fields = ('student', 'course', 'teacher', 'last_modified_by')
    # 或者，如果你的 Django 版本支持，可以尝试 autocomplete_fields (通常需要相关模型Admin也配置了search_fields)
    # autocomplete_fields = ('student', 'course', 'teacher', 'last_modified_by')

    readonly_fields = ('entry_time', 'last_modified_time') # 这些字段通常是自动设置的

    # 自定义方法以在 list_display 中显示更友好的名称
    def student_name_display(self, obj):
        return obj.student.name if obj.student else '-'
    student_name_display.short_description = '学生姓名' # 列的显示名称
    student_name_display.admin_order_field = 'student__name' # 允许按此列排序

    def course_name_display(self, obj):
        return obj.course.name if obj.course else '-'
    course_name_display.short_description = '课程名称'
    course_name_display.admin_order_field = 'course__name'

    def teacher_name_display(self, obj):
        return obj.teacher.name if obj.teacher else '-'
    teacher_name_display.short_description = '授课教师'
    teacher_name_display.admin_order_field = 'teacher__name'

    # fieldsets 可以用来组织表单的布局
    fieldsets = (
        ('成绩核心信息', {
            'fields': ('student', 'course', 'teacher', 'term', 'score')
        }),
        ('记录信息', {
            'fields': ('entry_time', 'last_modified_by', 'last_modified_time'),
            'classes': ('collapse',) # 默认折叠这个区域
        }),
    )