from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib import messages
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import Student as StudentProfile
from .models import Teacher as TeacherProfile
from .models import CustomUser

from .serializers import (
    CustomUserSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
    UserSelfUpdateSerializer,
    LoginSerializer,
    StudentProfileSelfUpdateSerializer,
    TeacherProfileSelfUpdateSerializer
)
from .permissions import IsAdminRole, IsOwnerOrAdminOnly, IsStudentRole, IsTeacherRole
from .forms import CustomAuthenticationForm

CustomUser = get_user_model()

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


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
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
            if (non_field_errors and isinstance(non_field_errors, list) and non_field_errors):
                error_message = str(non_field_errors[0])
        return Response(
            {"status": "error", "message": error_message},
            status=status.HTTP_400_BAD_REQUEST,
        )

class LogoutAPIView(APIView):
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


class UserLoginView(LoginView):
    template_name = 'users/login.html'
    authentication_form = CustomAuthenticationForm

    def form_invalid(self, form):
        messages.error(self.request, "用户名或密码不正确，请重试。")
        return super().form_invalid(form)

class UserLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        messages.success(request, "您已成功登出。")
        return response


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
    
    def get_serializer_class(self):
        user = self.request.user
        if self.action in ['update', 'partial_update'] and user.is_authenticated and user.role == CustomUser.Role.STUDENT:
            return StudentProfileSelfUpdateSerializer
        return StudentProfileSerializer
    
    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [permissions.IsAuthenticated, IsAdminRole | IsTeacherRole]
        elif self.action == 'create':
            permission_classes = [IsAdminRole]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_update(self, serializer):
        serializer.save()


class TeacherProfileViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_superuser or user.role == CustomUser.Role.ADMIN:
                return TeacherProfile.objects.select_related('user', 'department').all().order_by('user__username')
            elif user.role == CustomUser.Role.TEACHER:
                return TeacherProfile.objects.select_related('user', 'department').filter(user=user)
        return TeacherProfile.objects.none()

    def get_serializer_class(self):
        user = self.request.user
        if self.action in ['update', 'partial_update'] and user.is_authenticated and user.role == CustomUser.Role.TEACHER:
            return TeacherProfileSelfUpdateSerializer
        return TeacherProfileSerializer
    
    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [IsAdminRole]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_update(self, serializer):
        serializer.save()
