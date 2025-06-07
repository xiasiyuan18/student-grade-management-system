# student_grade_management_system/users/views.py

from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView # 导入传统的Django认证视图
from django.urls import reverse_lazy # 用于重定向
from django.contrib import messages # 用于Django messages框架


from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

# 导入您的 Profile 模型和 CustomUser 模型
from .models import Student as StudentProfile
from .models import Teacher as TeacherProfile
from .models import CustomUser # 确保 CustomUser 模型被导入

# 导入序列化器
from .serializers import (
    CustomUserSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
    UserSelfUpdateSerializer,
    LoginSerializer,  # LoginAPIView 会用
    StudentProfileSelfUpdateSerializer,
    TeacherProfileSelfUpdateSerializer
)
from .permissions import IsAdminRole, IsOwnerOrAdminOnly, IsStudentRole, IsTeacherRole
# 导入 CustomAuthenticationForm
from .forms import CustomAuthenticationForm # <-- 新增：从 forms.py 导入 CustomAuthenticationForm


# 获取自定义的用户模型
CustomUser = get_user_model()


# --- JWT Token生成辅助函数 ---
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["name"] = user.get_full_name()

    if user.is_superuser:
        refresh["ui_role"] = CustomUser.Role.ADMIN
    else:
        refresh["ui_role"] = user.role

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# =============================================================================
# DRF 认证相关的视图 (登录、登出) - 用于API
# =============================================================================

class LoginAPIView(APIView):
    """
    统一登录API视图。
    接收用户名(学号/工号/管理员名)和密码，返回JWT token和用户信息。
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            tokens = get_tokens_for_user(user)
            user_data = {
                "id": user.pk,
                "username": user.username,
                "name": user.get_full_name(),
                "role": user.role,
            }
            if user.role == CustomUser.Role.STUDENT:
                try:
                    user_data["student_id_num"] = user.student_profile.student_id_num
                except CustomUser.student_profile.RelatedObjectDoesNotExist:
                    user_data["student_id_num"] = None
            elif user.role == CustomUser.Role.TEACHER:
                try:
                    user_data["teacher_id_num"] = user.teacher_profile.teacher_id_num
                except CustomUser.teacher_profile.RelatedObjectDoesNotExist:
                    user_data["teacher_id_num"] = None
            if user.is_superuser or user.role == CustomUser.Role.ADMIN:
                user_data["is_admin_ui"] = True
            return Response(
                {
                    "status": "success",
                    "message": "登录成功",
                    "tokens": tokens,
                    "user": user_data,
                },
                status=status.HTTP_200_OK,
            )
        error_message = "用户名或密码有误"
        if serializer.errors:
            non_field_errors = serializer.errors.get("non_field_errors")
            if (
                non_field_errors
                and isinstance(non_field_errors, list)
                and non_field_errors
            ):
                error_message = str(non_field_errors[0])
            else:
                pass
        return Response(
            {
                "status": "error",
                "message": error_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class LogoutAPIView(APIView):
    """
    登出API视图。
    对于JWT，通常是将Refresh Token加入黑名单。
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"detail": "必须提供Refresh token。"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"status": "success", "message": "已成功登出"},
                status=status.HTTP_200_OK,
            )
        except TokenError as e:
            return Response(
                {"detail": "提供的Refresh token无效或已过期。"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"detail": "登出时发生错误。"}, status=status.HTTP_400_BAD_REQUEST
            )


# =============================================================================
# 传统 Django 认证视图 (用于渲染模板)
# =============================================================================

# 使用 Django 内置的 LoginView
class UserLoginView(LoginView):
    template_name = 'registration/login.html' # 指定模板路径
    authentication_form = CustomAuthenticationForm # <-- 使用自定义表单

    def form_invalid(self, form):
        messages.error(self.request, "用户名或密码不正确，请重试。")
        return super().form_invalid(form)


# 使用 Django 内置的 LogoutView
class UserLogoutView(LogoutView):
    # next_page 可以在 settings.py 中通过 LOGOUT_REDIRECT_URL 配置
    # 或者在这里明确指定：next_page = reverse_lazy('login') # 登出后返回登录页

    def dispatch(self, request, *args, **kwargs):
        # Add a success message after logout
        response = super().dispatch(request, *args, **kwargs)
        messages.success(request, "您已成功登出。")
        return response


# =============================================================================
# DRF ViewSets (用于API)
# =============================================================================

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by('username')

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update'] and \
           not (self.request.user.is_staff or \
                self.request.user.role == CustomUser.Role.ADMIN or \
                self.request.user.is_superuser):
            return UserSelfUpdateSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'create':
            permission_classes = [IsAdminRole]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOnly]
        elif self.action == 'destroy':
            permission_classes = [IsAdminRole]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = CustomUserSerializer(user, context={'request': request})
        return Response(serializer.data)


class StudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return StudentProfile.objects.none()

        if user.role == CustomUser.Role.ADMIN or user.is_staff or user.role == CustomUser.Role.TEACHER:
            return StudentProfile.objects.select_related('user', 'department', 'major').all().order_by('user__username')
        elif user.role == CustomUser.Role.STUDENT:
            return StudentProfile.objects.select_related('user', 'department', 'major').filter(user=user)
        return StudentProfile.objects.none()

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [permissions.IsAuthenticated, IsAdminRole | IsTeacherRole]
        elif self.action == 'create':
            permission_classes = [IsAdminRole]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            if self.request.method in permissions.SAFE_METHODS:
                 if self.action == 'retrieve':
                     permission_classes = [permissions.IsAuthenticated]
                 else:
                    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOnly]
            else:
                 permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOnly]
        elif self.action == 'destroy':
            permission_classes = [IsAdminRole]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        if user.role == CustomUser.Role.STUDENT and instance.user == user:
            allowed_fields_for_student_update = ['name', 'id_card', 'gender', 'birth_date', 'phone', 'dormitory', 'home_address']
            for field in list(serializer.validated_data.keys()):
                if field not in allowed_fields_for_student_update and field not in ['user']:
                    pass
        serializer.save()

    def get_serializer_class(self):
        user = self.request.user
        instance = self.get_object() if self.action in ['retrieve', 'update', 'partial_update'] else None
        if self.action in ['update', 'partial_update'] and \
           user.is_authenticated and user.role == CustomUser.Role.STUDENT and \
           instance and instance.user == user:
            return StudentProfileSelfUpdateSerializer
        return StudentProfileSerializer


class TeacherProfileViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return TeacherProfile.objects.none()

        if user.role == CustomUser.Role.ADMIN or user.is_staff:
            return TeacherProfile.objects.select_related('user', 'department').all().order_by('user__username')
        elif user.role == CustomUser.Role.TEACHER:
            return TeacherProfile.objects.select_related('user', 'department').filter(user=user)
        return TeacherProfile.objects.none()

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [IsAdminRole]
        elif self.action == 'create':
            permission_classes = [IsAdminRole]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOnly]
        elif self.action == 'destroy':
            permission_classes = [IsAdminRole]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        if user.role == CustomUser.Role.TEACHER and instance.user == user:
            allowed_fields_for_teacher_update = ['name']
            for field in list(serializer.validated_data.keys()):
                if field not in allowed_fields_for_teacher_update and field not in ['user']:
                    pass
        serializer.save()

    def get_serializer_class(self):
        user = self.request.user
        instance = self.get_object() if self.action in ['retrieve', 'update', 'partial_update'] else None
        if self.action in ['update', 'partial_update'] and \
           user.is_authenticated and user.role == CustomUser.Role.TEACHER and \
           instance and instance.user == user:
            return TeacherProfileSelfUpdateSerializer
        return TeacherProfileSerializer