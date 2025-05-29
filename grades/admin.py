# grades/admin.py

from django.contrib import admin
from django.urls import reverse # 用于在 admin 中生成其他 admin 页面的链接
from django.utils.html import format_html # 用于在 admin 中格式化 HTML 输出

# 从正确的应用导入模型
from .models import Grade # Grade 模型在当前应用的 models.py 中
# from courses.models import TeachingAssignment # 只有在自定义表单且不使用 raw_id_fields 时才可能需要直接导入
# from users.models import Student # 只有在自定义表单且不使用 raw_id_fields 时才可能需要直接导入

@admin.register(Grade) # 使用装饰器注册 GradeAdmin，这是唯一注册 Grade 模型的地方
class GradeAdmin(admin.ModelAdmin):
    # --- 在列表视图中显示的列 ---
    list_display = (
        'student_link',        # 自定义方法，显示学生并链接到学生Admin详情页
        'get_course_name',     # 自定义方法，显示课程名称
        'get_teacher_name',    # 自定义方法，显示教师名称
        'get_term',            # 自定义方法，显示学期
        'score',
        'last_modified_by_display', # 自定义方法，显示最后修改人
        'last_modified_time',
        'entry_time',
    )

    # --- 右侧边栏的过滤器 ---
    list_filter = (
        'teaching_assignment__semester',        # 按授课安排的学期过滤
        # 使用 RelatedOnlyFieldListFilter 可以让过滤器只显示那些实际在成绩记录中出现过的关联对象
        ('teaching_assignment__course', admin.RelatedOnlyFieldListFilter),
        ('teaching_assignment__teacher', admin.RelatedOnlyFieldListFilter),
        ('student__department', admin.RelatedOnlyFieldListFilter),
        ('student__major', admin.RelatedOnlyFieldListFilter),
    )

    # --- 可搜索的字段 ---
    search_fields = (
        'student__user__username',          # 搜索学生的登录用户名
        'student__name',                    # 搜索学生的姓名 (假设 Student 模型有 name 字段)
        'student__student_id_num',          # 搜索学号 (假设 Student 模型有 student_id_num 字段)
        'teaching_assignment__course__course_id',   # 搜索课程编号
        'teaching_assignment__course__course_name', # 搜索课程名称
        'teaching_assignment__teacher__user__username',# 搜索教师的登录用户名
        'teaching_assignment__teacher__name',        # 搜索教师姓名 (假设 Teacher 模型有 name 字段)
        'teaching_assignment__teacher__teacher_id_num',# 搜索教师工号 (假设 Teacher 模型有 teacher_id_num 字段)
        'teaching_assignment__semester',             # 搜索学期
        'score',                                     # 直接搜索分数
    )

    # --- 对于外键字段，使用原始ID输入框 (当关联对象非常多时可以提升性能) ---
    raw_id_fields = (
        'student',
        'teaching_assignment',
        'last_modified_by', # 如果用户量很大，这个字段也建议使用 raw_id_fields
    )

    # --- 优化列表视图的数据库查询 ---
    list_select_related = (
        'student__user',                # 为了 student_link 和基于学生用户名的搜索
        'student__department',          # 为了 list_filter
        'student__major',               # 为了 list_filter
        'teaching_assignment__course',  # 为了 get_course_name, list_filter, 和基于课程的搜索
        'teaching_assignment__teacher__user', # 为了 get_teacher_name, list_filter, 和基于教师用户的搜索
        'last_modified_by',             # 为了 last_modified_by_display
    )

    # --- 在详情页中设置为只读的字段 ---
    # auto_now_add 和 auto_now 字段通常是只读的
    readonly_fields = ('entry_time', 'last_modified_time')

    # --- 自定义方法，用于在 list_display 中更好地显示关联数据 ---
    def student_link(self, obj):
        if obj.student and obj.student.user:
            # 确保这里的 app_label 和 model_name 与你的 Student 模型一致
            # 通常是 'users_student_change' 或 'your_app_name_student_change'
            # obj.student._meta.app_label 会获取 Student 模型所在的 app 的名称
            # obj.student._meta.model_name 会获取 Student 模型的名称 (小写)
            try:
                student_admin_url_name = f"admin:{obj.student._meta.app_label}_{obj.student._meta.model_name}_change"
                url = reverse(student_admin_url_name, args=[obj.student.pk])
                # 使用 Student 模型的 name 字段，如果不存在则用 username，并显示学号
                display_name = obj.student.name or obj.student.user.username
                display_id = obj.student.student_id_num or ""
                return format_html('<a href="{}">{} ({})</a>', url, display_name, display_id)
            except Exception: # 捕获可能的 NoReverseMatch 等错误
                return str(obj.student) # 出错时回退到默认字符串表示
        return "-" # 如果没有关联学生
    student_link.short_description = '学生 (学号)' # Admin 后台显示的列名
    student_link.admin_order_field = 'student__name' # 允许按学生姓名排序 (假设 Student 有 name 字段)

    def get_course_name(self, obj):
        if obj.teaching_assignment and obj.teaching_assignment.course:
            return obj.teaching_assignment.course.course_name # 假设 Course 有 course_name 字段
        return None
    get_course_name.short_description = '课程名称'
    get_course_name.admin_order_field = 'teaching_assignment__course__course_name' # 允许按课程名称排序

    def get_teacher_name(self, obj):
        if obj.teaching_assignment and obj.teaching_assignment.teacher:
            return str(obj.teaching_assignment.teacher) # 依赖 Teacher 模型的 __str__ 方法
        return None
    get_teacher_name.short_description = '授课教师'
    get_teacher_name.admin_order_field = 'teaching_assignment__teacher__name' # 允许按教师姓名排序 (假设 Teacher 有 name 字段)

    def get_term(self, obj):
        if obj.teaching_assignment:
            return obj.teaching_assignment.semester
        return None
    get_term.short_description = '学期'
    get_term.admin_order_field = 'teaching_assignment__semester' # 允许按学期排序

    def last_modified_by_display(self, obj):
        if obj.last_modified_by:
            return obj.last_modified_by.username # 显示最后修改人的用户名
        return "-"
    last_modified_by_display.short_description = '最后修改人'
    last_modified_by_display.admin_order_field = 'last_modified_by__username' # 允许按用户名排序

    # 如果需要，可以在这里添加 fieldsets 来自定义详情页的布局
    # fieldsets = (
    #     (None, {
    #         'fields': ('student', 'teaching_assignment', 'score')
    #     }),
    #     ('元数据', {
    #         'fields': ('last_modified_by', 'last_modified_time', 'entry_time'),
    #         'classes': ('collapse',), # 可折叠
    #     }),
    # )

    # --- 确保此文件中没有其他 admin.site.register(Grade, ...) 的调用 ---
    # 上方的 @admin.register(Grade) 装饰器已经完成了注册。