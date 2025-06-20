# users/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model

CustomUser = get_user_model() # 获取你的自定义用户模型

class IsAdminOrReadOnly(BasePermission):
    """
    自定义权限：允许管理员进行所有操作，其他已认证用户只读。
    """
    def has_permission(self, request, view):
        # 对列表视图（List views），所有已认证用户都有读取权限
        if request.method in SAFE_METHODS: # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
            return request.user and request.user.is_authenticated
        # 对于写操作 (POST, PUT, PATCH, DELETE)，只允许管理员
        return request.user and request.user.is_staff # 或者 request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        # 对详情视图（Detail views），所有已认证用户都有读取权限
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # 对于写操作，只允许管理员
        return request.user and request.user.is_staff


class IsOwnerOrAdminOnly(BasePermission):
    """
    自定义权限：只允许对象的所有者或管理员进行编辑和删除操作。
    其他已认证用户可能有读取权限（取决于视图级别的 has_permission）。
    """
    def has_object_permission(self, request, view, obj):
        # 读取权限通常在视图级别的 has_permission 中处理，
        # 或者如果默认是 IsAuthenticated，那么所有人都能读。
        # 如果想在这里也限制读取，可以取消下面的注释：
        # if request.method in SAFE_METHODS:
        #     return True # 或者更细致的检查

        # 写权限只给对象所有者或管理员
        # 假设对象 obj 有一个 user 字段指向创建者 (CustomUser)
        # 或者你的 Profile 模型 (Student, Teacher) 有一个 user 字段
        if hasattr(obj, 'user'): # 例如 Student Profile, Teacher Profile
            return obj.user == request.user or request.user.is_staff
        elif isinstance(obj, CustomUser): # 如果对象本身就是 CustomUser
            return obj == request.user or request.user.is_staff
        # 如果对象没有 user 字段，但有其他方式判断所有者，在此添加逻辑
        # 例如，如果 Grade 对象的 student 字段是 Student Profile 实例
        elif hasattr(obj, 'student') and hasattr(obj.student, 'user'):
            return obj.student.user == request.user or request.user.is_staff

        return request.user and request.user.is_staff # 默认只有管理员可操作无主对象


class IsStudentRole(BasePermission):
    """
    检查用户是否为学生角色。
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == CustomUser.Role.STUDENT

    # 通常角色检查是视图级别的，如果需要对象级别，也可以实现 has_object_permission
    # def has_object_permission(self, request, view, obj):
    #     # ... (如果需要基于对象和学生角色进行判断) ...
    #     return self.has_permission(request, view)


class IsTeacherRole(BasePermission):
    """
    检查用户是否为教师角色。
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == CustomUser.Role.TEACHER

    # def has_object_permission(self, request, view, obj):
    #     # ...
    #     return self.has_permission(request, view)

# 对于管理员角色，通常可以直接使用 DRF 内建的 permissions.IsAdminUser
# from rest_framework.permissions import IsAdminUser
# 如果你的 CustomUser 的 is_staff 字段能准确代表管理员，那么 IsAdminUser 就够用。
# 如果你想基于 CustomUser.Role.ADMIN 来判断，可以创建一个类似的 IsAdminRole。

class IsAdminRole(BasePermission):
    """
    检查用户是否为管理员角色 (基于 CustomUser.role 字段)。
    """
    def has_permission(self, request, view):
        # 同时检查 is_staff 可能是个好主意，因为管理员通常也应该是 staff
        return request.user.is_authenticated and hasattr(request.user, 'role') and \
               (request.user.role == CustomUser.Role.ADMIN or request.user.is_superuser)

    # def has_object_permission(self, request, view, obj):
    #     return self.has_permission(request, view)


# ✅ 新增：添加缺失的权限检查函数
def is_admin_or_teacher_or_manager(user):
    """
    检查用户是否为管理员、教师或管理人员。
    这个函数用于视图中的权限检查。
    """
    if not user.is_authenticated:
        return False
    
    # 检查是否为超级用户或管理员
    if user.is_superuser or user.is_staff:
        return True
    
    # 检查用户角色
    if hasattr(user, 'role'):
        return user.role in [CustomUser.Role.ADMIN, CustomUser.Role.TEACHER]
    
    return False