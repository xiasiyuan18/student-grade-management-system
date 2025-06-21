from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect
from users.models import CustomUser


def role_required(allowed_roles):
    """
    角色权限装饰器
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "请先登录")
                return redirect('login')
            
            user_role = getattr(request.user, 'role', None)
            if user_role not in allowed_roles:
                messages.error(request, "您没有访问此页面的权限")
                return redirect('home')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def student_required(view_func):
    """学生权限装饰器"""
    return role_required([CustomUser.Role.STUDENT])(view_func)


def teacher_required(view_func):
    """教师权限装饰器"""
    return role_required([CustomUser.Role.TEACHER])(view_func)


def admin_required(view_func):
    """管理员权限装饰器"""
    return role_required([CustomUser.Role.ADMIN])(view_func)


def teacher_or_admin_required(view_func):
    """教师或管理员权限装饰器"""
    return role_required([CustomUser.Role.TEACHER, CustomUser.Role.ADMIN])(view_func)