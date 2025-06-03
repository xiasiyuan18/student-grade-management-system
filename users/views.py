from django.contrib.auth import (  # update_session_auth_hash 可能用不到（JWT场景）
    get_user_model, update_session_auth_hash)
from rest_framework import permissions, status, viewsets  # status 需要导入
from rest_framework.decorators import action  # 如果 ViewSet 中有自定义 action
from rest_framework.response import Response  # Response 需要导入
from rest_framework.views import APIView  # APIView 需要导入
# 导入JWT相关的工具 (假设您将 get_tokens_for_user 放在了 utils.py 或直接在此处定义)
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

# 导入您的 Profile 模型和 CustomUser 模型
from .models import Student as StudentProfile  # 使用 Profile 别名
from .models import Teacher as TeacherProfile
# 导入序列化器
from .serializers import (
    CustomUserSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
    UserSelfUpdateSerializer,
    LoginSerializer, # LoginAPIView 会用
    UserSelfUpdateSerializer,
    StudentProfileSelfUpdateSerializer,
    TeacherProfileSelfUpdateSerializer 
)
from .permissions import IsAdminRole, IsOwnerOrAdminOnly, IsStudentRole, IsTeacherRole
from .serializers import (CustomUserSerializer, StudentProfileSerializer,
                          TeacherProfileSerializer)

from .models import CustomUser # get_user_model() 已经获取了


CustomUser = get_user_model()


# --- JWT Token生成辅助函数 (可以放在 utils.py) ---
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    # 在token的payload中添加自定义声明 (claims)
    refresh["role"] = user.role
    refresh["name"] = user.get_full_name()  # 或者 user.name，取决于 CustomUser 定义

    # 根据角色进一步细化UI上显示的角色或权限标识
    if user.is_superuser:
        refresh["ui_role"] = CustomUser.Role.ADMIN
    else:
        refresh["ui_role"] = user.role

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# =============================================================================
# 认证相关的视图 (登录、登出)
# =============================================================================


class LoginAPIView(APIView):
    """
    统一登录API视图。
    接收用户名(学号/工号/管理员名)和密码，返回JWT token和用户信息。
    """

    permission_classes = [permissions.AllowAny]  # 允许任何人访问登录接口
    serializer_class = LoginSerializer  # 使用您为JWT登录设计的 LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = serializer.validated_data["user"]  # 获取已认证的 CustomUser 对象

            tokens = get_tokens_for_user(user)  # 为该用户生成JWT Token

            # 构建成功响应的用户信息部分
            user_data = {
                "id": user.pk,  # 或者 user.username
                "username": user.username,  # CustomUser 的登录名
                "name": user.get_full_name(),
                "role": user.role,  # CustomUser 中定义的角色
            }

            # 根据角色尝试附加 Profile 中的特定ID (学号/工号)
            if user.role == CustomUser.Role.STUDENT:
                try:
                    user_data["student_id_num"] = user.student_profile.student_id_num
                except CustomUser.student_profile.RelatedObjectDoesNotExist:
                    user_data["student_id_num"] = None  # Profile 可能尚未创建
            elif user.role == CustomUser.Role.TEACHER:
                try:
                    user_data["teacher_id_num"] = user.teacher_profile.teacher_id_num
                except CustomUser.teacher_profile.RelatedObjectDoesNotExist:
                    user_data["teacher_id_num"] = None

            # 如果是管理员角色，前端可能需要一个明确的标识
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

        # 验证失败，LoginSerializer 会抛出 ValidationError，DRF默认会处理成400
        # 为了返回统一的错误格式，可以这样：
        error_message = "用户名或密码有误"
        if serializer.errors:  # 如果有具体的错误信息
            # 通常 serializer.errors 是一个字典，例如 {'non_field_errors': ['错误信息']}
            # 我们可以取第一条非字段错误
            non_field_errors = serializer.errors.get("non_field_errors")
            if (
                non_field_errors
                and isinstance(non_field_errors, list)
                and non_field_errors
            ):
                error_message = str(non_field_errors[0])
            else:  # 如果没有非字段错误，可能是字段级错误，但也统一提示
                # 或者你想更细致地显示 serializer.errors.get('username') 或 .get('password')
                # 但通常登录不建议太具体
                pass

        return Response(
            {
                "status": "error",
                "message": error_message,
                # "details": serializer.errors # 生产环境可以考虑不返回详细的details
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class LogoutAPIView(APIView):
    """
    登出API视图。
    对于JWT，通常是将Refresh Token加入黑名单。
    """

    permission_classes = [permissions.IsAuthenticated]  # 只有登录用户才能登出

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"detail": "必须提供Refresh token。"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()  # 将 refresh token 加入黑名单 (需要在 settings.py 中配置 'rest_framework_simplejwt.token_blacklist')

            return Response(
                {"status": "success", "message": "已成功登出"},
                status=status.HTTP_200_OK,
            )  # 或者 HTTP_204_NO_CONTENT
        except TokenError as e:
            # print(f"TokenError on logout: {e}") # 调试用
            return Response(
                {"detail": "提供的Refresh token无效或已过期。"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # print(f"Exception on logout: {e}") # 调试用
            return Response(
                {"detail": "登出时发生错误。"}, status=status.HTTP_400_BAD_REQUEST
            )


from django.contrib.auth import get_user_model  # 用于获取 AUTH_USER_MODEL
from rest_framework import permissions, viewsets

from .models import (Student,  # 导入你的 Student Profile 和 Teacher Profile 模型
                     Teacher)
from .serializers import (CustomUserSerializer,  # 确保你已经在 serializers.py 中定义了这些
                          StudentProfileSerializer, TeacherProfileSerializer)

CustomUser = get_user_model()  # 获取你在 settings.py 中定义的 AUTH_USER_MODEL


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by('username')
    # serializer_class = CustomUserSerializer # 将在 get_serializer_class 中动态选择

    def get_serializer_class(self):
        # 普通用户更新自己信息时，使用限制性更强的序列化器
        if self.action in ['update', 'partial_update'] and \
           not (self.request.user.is_staff or \
                self.request.user.role == CustomUser.Role.ADMIN or \
                self.request.user.is_superuser):
            return UserSelfUpdateSerializer # 只允许修改姓名、邮箱等
        return CustomUserSerializer # 管理员使用完整功能的序列化器

    def get_permissions(self):
        # 将 'list' action 的权限从 IsAdminRole 改为 IsAuthenticated
        if self.action == 'list':
            # 允许任何已认证用户查看教师列表
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

    # 不允许普通用户修改自己的角色、is_staff, is_superuser, is_active 等
    # 这通常通过 UserSelfUpdateSerializer 的 fields/read_only_fields 控制
    # 或者在 perform_update 中进行检查和剥离

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        user = request.user
        # 使用 get_serializer_class 来获取适合当前用户的序列化器
        # 但通常 "me" 端点返回的是较全的信息，所以可以直接用 CustomUserSerializer
        # 如果希望 "me" 也遵循 UserSelfUpdateSerializer 的字段限制，则用 self.get_serializer(user)
        serializer = CustomUserSerializer(user, context={'request': request})
        return Response(serializer.data)




class StudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer
    # queryset 会在 get_queryset 中定义

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return StudentProfile.objects.none()

        if user.role == CustomUser.Role.ADMIN or user.is_staff or user.role == CustomUser.Role.TEACHER:
            # 管理员和教师可以查看所有学生档案
            return StudentProfile.objects.select_related('user', 'department', 'major').all().order_by('user__username')
        elif user.role == CustomUser.Role.STUDENT:
            # 学生只能查看自己的档案
            return StudentProfile.objects.select_related('user', 'department', 'major').filter(user=user)
        return StudentProfile.objects.none()

    def get_permissions(self):
        if self.action == 'list':
            # 管理员和教师可以查看列表
            permission_classes = [permissions.IsAuthenticated, IsAdminRole | IsTeacherRole]
        elif self.action == 'create':
            # 通常学生档案与CustomUser一起创建，或由管理员创建
            permission_classes = [IsAdminRole]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            # 学生能看/改自己的，管理员能看/改所有，教师可能只能看 (IsOwnerOrAdminOnly 需要调整或组合)
            # IsOwnerOrAdminOnly 检查 obj.user == request.user 或 request.user是管理员
            # 对于学生修改自己的档案，这个权限适用。
            # 对于教师查看学生档案，需要在 IsOwnerOrAdminOnly 的 SAFE_METHODS 部分允许，
            # 或者为教师查看详情单独设置权限。
            # 一个简单的组合：
            if self.request.method in permissions.SAFE_METHODS: # GET, HEAD, OPTIONS
                # 允许学生看自己的，教师看所有，管理员看所有
                permission_classes = [permissions.IsAuthenticated, IsStudentRole | IsTeacherRole | IsAdminRole]
                # 但 IsOwnerOrAdminOnly 已经处理了 obj.user == request.user，所以学生能看自己的
                # 教师查看的权限由 get_queryset 控制了，所以 IsAuthenticated 可能就够了，然后 IsOwnerOrAdminOnly 控制写操作
                # 更精确的：
                if self.action == 'retrieve':
                     # 学生看自己的，教师看他班的（需自定义权限），管理员看所有
                     # 暂时简化：IsAuthenticated 配合 get_queryset, 写操作用 IsOwnerOrAdminOnly
                     permission_classes = [permissions.IsAuthenticated]
                else: # update, partial_update
                    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOnly]
            else: # 写操作 (PUT, PATCH)
                 permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOnly] # 学生只能改自己的，管理员可以改所有
        elif self.action == 'destroy':
            permission_classes = [IsAdminRole]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_update(self, serializer):
        # 学生修改自己信息时，不能修改“身份”相关的字段，例如 student_id_num, major, department等
        # 这应该在 StudentProfileSerializer 中将这些字段对非管理员用户设为 read_only，
        # 或者在这里根据用户角色剥离 validated_data 中的敏感字段。
        instance = serializer.instance
        user = self.request.user
        if user.role == CustomUser.Role.STUDENT and instance.user == user:
            # 学生正在修改自己的档案
            allowed_fields_for_student_update = ['name', 'id_card', 'gender', 'birth_date', 'phone', 'dormitory', 'home_address'] # 示例
            # 实际可修改字段由 StudentSelfUpdateSerializer (如果创建的话) 控制更好
            # 或者在这里检查 validated_data 的键
            for field in list(serializer.validated_data.keys()):
                if field not in allowed_fields_for_student_update and field not in ['user']: # user通常不能直接修改
                    # 如果 serializer 级别没有做限制，可以在这里 pop
                    # raise PermissionDenied(f"学生不能修改字段: {field}")
                    pass # 更好的做法是让序列化器处理字段限制
        serializer.save()
        
    def get_serializer_class(self):
        user = self.request.user
        instance = self.get_object() if self.action in ['retrieve', 'update', 'partial_update'] else None
        if self.action in ['update', 'partial_update'] and \
           user.is_authenticated and user.role == CustomUser.Role.STUDENT and \
           instance and instance.user == user:
            return StudentProfileSelfUpdateSerializer
        return StudentProfileSerializer # 其他情况（如管理员操作或查看）使用完整序列化器

class TeacherProfileViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherProfileSerializer
    # queryset 会在 get_queryset 中定义

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
        # 教师修改自己信息时，不能修改“身份”相关的字段，例如 teacher_id_num, department
        # 同样，最好由 TeacherSelfUpdateSerializer 控制，或在此检查
        instance = serializer.instance
        user = self.request.user
        if user.role == CustomUser.Role.TEACHER and instance.user == user:
            allowed_fields_for_teacher_update = ['name'] # 示例，教师通常只能改姓名，密码通过专门接口
            # 实际可修改字段由 TeacherSelfUpdateSerializer (如果创建的话) 控制更好
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



from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser  # 导入您的 CustomUser 模型


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    # 在token的payload中添加自定义声明 (claims)，例如用户的角色
    # 这样前端拿到access token后，可以直接解码获取角色信息，无需再次请求
    refresh["role"] = user.role  # 直接从 CustomUser 获取角色
    # refresh['name'] = user.get_full_name() # 可以添加姓名等

    # 如果需要区分管理员角色 (即使 role 是 TEACHER 或 STUDENT，但他们可能是is_superuser)
    if user.is_superuser:
        refresh["actual_role_for_ui"] = CustomUser.Role.ADMIN
    else:
        refresh["actual_role_for_ui"] = user.role

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
