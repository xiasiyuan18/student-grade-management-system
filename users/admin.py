from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Student # 假设你的 Teacher 模型也在这里，或者在 teachers 应用中
# from .models import Teacher # 如果 Teacher 模型在 users 应用中

@admin.register(Student)
class StudentAdmin(BaseUserAdmin):
    # UserAdmin 已经有很多预设，这里可以覆盖或添加
    # fieldsets 通常用来组织表单字段。你需要确保所有 Student 模型中
    # REQUIRED_FIELDS 和 USERNAME_FIELD 以及其他自定义字段都包含在内。
    # 下面是一个基于 UserAdmin 并加入你 Student 模型字段的示例，你需要调整
    # 以匹配你 Student 模型的具体字段。

    # UserAdmin 的默认 fieldsets 结构:
    # (None, {'fields': ('username', 'password')}),
    # ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
    # ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    # ('Important dates', {'fields': ('last_login', 'date_joined')}),

    # 你需要根据 Student 模型的字段来调整 fieldsets
    # 例如，你的 USERNAME_FIELD 是 'student_id'
    fieldsets = (
        (None, {'fields': ('student_id', 'password')}), # USERNAME_FIELD 和 password
        ('个人信息', {'fields': ('name', 'id_card', 'gender', 'birth_date', 'phone', 'home_address', 'dormitory')}),
        ('学籍信息', {'fields': ('grade', 'major_id', 'department_id', 'minor_department_id', 'degree_level', 'credits_earned')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    # list_display 控制在列表页显示哪些字段
    list_display = ('student_id', 'name', 'grade', 'major_id', 'is_staff')
    search_fields = ('student_id', 'name', 'id_card')
    ordering = ('student_id',)

    # 如果 Student 模型有新增的字段不在 UserAdmin 的默认 add_fieldsets 中，
    # 你也需要在这里为用户创建表单（add_form）调整它们。
    # add_fieldsets 主要用于用户创建表单。
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('额外信息', {
            'fields': ('name', 'id_card', 'gender', 'birth_date', # ... 以及 Student 的其他必填或可选字段
                       'grade', 'major_id', 'department_id', 'degree_level'
                      ),
        }),
    )
    # 如果你的 Student 模型直接就是 AUTH_USER_MODEL，并且你没有使用 Django 默认的 User 模型的字段
    # (如 first_name, last_name, email)，你需要确保 UserAdmin 使用的字段与你的模型匹配。
    # 你可能需要创建一个自定义表单 (form 和 add_form) 来完全控制字段。

    # 注意：UserAdmin 是为 Django 的 User 模型设计的，它有很多内置的逻辑。
    # 当你用一个字段完全不同的自定义用户模型替换它时，可能需要更多调整。
    # 确保你的 Student 模型包含了 UserAdmin 期望的一些基本属性或方法，
    # 或者在 StudentAdmin 中覆盖相关方法。