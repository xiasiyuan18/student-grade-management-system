from django.contrib import admin
from django.contrib.auth.admin import \
    UserAdmin as BaseUserAdmin  # 导入基础 UserAdmin

from .models import CustomUser, Student, Teacher  # 确保从你的 models.py 中导入了这三个模型


# 1. 为 CustomUser 模型配置 Admin
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):

    list_display = BaseUserAdmin.list_display + ("role",)  # 在原有基础上增加 role
    list_filter = BaseUserAdmin.list_filter + ("role",)  # 按 role 筛选
    fieldsets_list = list(BaseUserAdmin.fieldsets)

    personal_info_index = -1
    for i, fieldset in enumerate(fieldsets_list):
        if fieldset[0] == "Personal info":
            personal_info_index = i
            break

    if personal_info_index != -1:
        personal_info_fields = list(fieldsets_list[personal_info_index][1]["fields"])
        if "role" not in personal_info_fields:  # 避免重复添加
            personal_info_fields.append("role")
        fieldsets_list[personal_info_index] = (
            "Personal info",
            {"fields": tuple(personal_info_fields)},
        )
    else:
        fieldsets_list.append(("角色信息", {"fields": ("role",)}))

    fieldsets = tuple(fieldsets_list)
    add_fieldsets_list = list(BaseUserAdmin.add_fieldsets)
    add_fieldsets_list.append(
        (
            "角色信息 (创建时)",
            {
                "classes": ("wide",),
                "fields": ("role",),
            },
        )
    )
    add_fieldsets = tuple(add_fieldsets_list)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "user",  # 显示关联的 CustomUser 对象 (会调用 CustomUser 的 __str__ 方法)
        "student_id_num",  # Student Profile 的学号字段
        "name",  # Student Profile 的姓名
        "grade_year",  # Student Profile 的年级字段
        "major",  # Student Profile 的专业外键 (会调用 Major 的 __str__ 方法)
        "department",  # Student Profile 的院系外键 (会调用 Department 的 __str__ 方法)
        "get_user_email",  # 自定义方法显示关联用户的邮箱
        "is_user_active",  # 自定义方法显示关联用户的激活状态
    )
    search_fields = (
        "student_id_num",
        "name",
        "user__username",
        "user__email",
    )  # 可以搜索 Profile 字段和关联 User 的字段
    list_filter = (
        "grade_year",
        "major",
        "department",
        "user__is_active",
    )  # 可以按 Profile 字段和关联 User 的字段筛选
    ordering = ["student_id_num"]  # 按学号排序

    # readonly_fields = ('user',) # 通常 Profile 的 user 字段在创建后不应直接修改

    # fieldsets 控制 Student Profile 编辑表单的布局
    fieldsets = (
        (
            "关联用户账户",
            {"fields": ("user",)},
        ),  
        (
            "学生基本信息",
            {
                "fields": (
                    "student_id_num",
                    "name",
                    "id_card",
                    "gender",
                    "birth_date",
                    "phone",
                )
            },
        ),
        ("住宿与地址", {"fields": ("dormitory", "home_address")}),
        (
            "学籍信息",
            {
                "fields": (
                    "grade_year",
                    "major",
                    "department",
                    "minor_department",
                    "degree_level",
                    "credits_earned",
                )
            },
        ),
    )

    # 定义获取关联 CustomUser 邮箱的方法
    @admin.display(description="用户邮箱", ordering="user__email")
    def get_user_email(self, obj):
        return obj.user.email

    # 定义获取关联 CustomUser 激活状态的方法
    @admin.display(description="账户是否激活", ordering="user__is_active", boolean=True)
    def is_user_active(self, obj):
        return obj.user.is_active


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "teacher_id_num",
        "name",
        "get_department_name",
        "get_user_email",
        "is_user_active",
    )
    search_fields = ("teacher_id_num", "name", "user__username", "user__email")
    list_filter = ("department", "user__is_active")
    ordering = ["teacher_id_num"]


    fieldsets = (
        ("关联用户账户", {"fields": ("user",)}),
        ("教师基本信息", {"fields": ("teacher_id_num", "name", "department")}),
    )

    @admin.display(
        description="所属院系", ordering="department__dept_name"
    )  
    def get_department_name(self, obj):
        if obj.department:
            return obj.department.dept_name
        return None

    @admin.display(description="用户邮箱", ordering="user__email")
    def get_user_email(self, obj):
        return obj.user.email

    @admin.display(description="账户是否激活", ordering="user__is_active", boolean=True)
    def is_user_active(self, obj):
        return obj.user.is_active
