from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from users.models import CustomUser


class RoleRequiredMixin(UserPassesTestMixin):
    """基础角色权限混入类"""
    required_role = None
    permission_denied_message = "您没有访问此页面的权限"
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        if self.required_role is None:
            return True
            
        return hasattr(self.request.user, 'role') and self.request.user.role == self.required_role
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, "请先登录")
            return redirect('login')
        else:
            messages.error(self.request, self.permission_denied_message)
            return redirect('home')


class StudentRequiredMixin(RoleRequiredMixin):
    """学生角色权限混入类"""
    required_role = CustomUser.Role.STUDENT
    permission_denied_message = "此页面仅限学生访问"


class TeacherRequiredMixin(RoleRequiredMixin):
    """教师角色权限混入类"""
    required_role = CustomUser.Role.TEACHER
    permission_denied_message = "此页面仅限教师访问"


class AdminRequiredMixin(RoleRequiredMixin):
    """管理员角色权限混入类"""
    required_role = CustomUser.Role.ADMIN
    permission_denied_message = "此页面仅限管理员访问"


class TeacherOrAdminMixin(UserPassesTestMixin):
    """教师或管理员权限混入类"""
    permission_denied_message = "此页面仅限教师或管理员访问"
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        user_role = getattr(self.request.user, 'role', None)
        return user_role in [CustomUser.Role.TEACHER, CustomUser.Role.ADMIN]
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, "请先登录")
            return redirect('login')
        else:
            messages.error(self.request, self.permission_denied_message)
            return redirect('home')


class OwnDataOnlyMixin:
    """只能访问自己数据的混入类"""
    
    def get_queryset(self):
        """限制查询集只返回与当前用户相关的数据"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # 如果是学生，只能查看自己的数据
        if hasattr(user, 'role') and user.role == CustomUser.Role.STUDENT:
            if hasattr(self.model, 'student'):
                # 对于有student字段的模型
                return queryset.filter(student__user=user)
            elif hasattr(self.model, 'user'):
                # 对于有user字段的模型
                return queryset.filter(user=user)
        
        # 如果是教师，只能查看自己教的课程相关数据
        elif hasattr(user, 'role') and user.role == CustomUser.Role.TEACHER:
            if hasattr(self.model, 'teaching_assignment'):
                # 对于成绩等与教学安排相关的模型
                return queryset.filter(teaching_assignment__teacher__user=user)
        
        # 管理员可以查看所有数据
        return queryset


class SensitiveInfoMixin:
    """敏感信息控制混入类"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 根据用户角色控制敏感信息显示
        if hasattr(user, 'role'):
            if user.role == CustomUser.Role.STUDENT:
                context['show_sensitive_info'] = False
                context['show_id_card'] = True  # 学生可以看到自己的身份证
            elif user.role == CustomUser.Role.TEACHER:
                context['show_sensitive_info'] = False
                context['show_id_card'] = False  # 教师不能看到学生身份证
            elif user.role == CustomUser.Role.ADMIN:
                context['show_sensitive_info'] = True
                context['show_id_card'] = True  # 管理员可以看到所有信息
        
        return context