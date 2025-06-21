from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model

CustomUser = get_user_model() 

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
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff
        elif isinstance(obj, CustomUser): # 如果对象本身就是 CustomUser
            return obj == request.user or request.user.is_staff
        elif hasattr(obj, 'student') and hasattr(obj.student, 'user'):
            return obj.student.user == request.user or request.user.is_staff

        return request.user and request.user.is_staff # 默认只有管理员可操作无主对象


class IsStudentRole(BasePermission):
    """
    检查用户是否为学生角色。
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == CustomUser.Role.STUDENT


class IsTeacherRole(BasePermission):
    """
    检查用户是否为教师角色。
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == CustomUser.Role.TEACHER


class IsAdminRole(BasePermission):
    """
    检查用户是否为管理员角色 (基于 CustomUser.role 字段)。
    """
    def has_permission(self, request, view):
       
        return request.user.is_authenticated and hasattr(request.user, 'role') and \
               (request.user.role == CustomUser.Role.ADMIN or request.user.is_superuser)



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