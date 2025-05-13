from rest_framework import viewsets, permissions, status # status 需要导入
from rest_framework.views import APIView # APIView 需要导入
from rest_framework.response import Response # Response 需要导入
from rest_framework.decorators import action # 如果 ViewSet 中有自定义 action
from django.contrib.auth import get_user_model, update_session_auth_hash # update_session_auth_hash 可能用不到（JWT场景）
# 导入您的 Profile 模型和 CustomUser 模型
from .models import Student as StudentProfile, Teacher as TeacherProfile # 使用 Profile 别名
# from .models import CustomUser # get_user_model() 已经获取了

# 导入序列化器
from .serializers import (
    CustomUserSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
    LoginSerializer # <--- 确保这个 LoginSerializer 是我们之前设计的，用于JWT登录
)

# 导入JWT相关的工具 (假设您将 get_tokens_for_user 放在了 utils.py 或直接在此处定义)
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
# from .utils import get_tokens_for_user # 如果放在 utils.py

CustomUser = get_user_model()

# --- JWT Token生成辅助函数 (可以放在 utils.py) ---
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    # 在token的payload中添加自定义声明 (claims)
    refresh['role'] = user.role
    refresh['name'] = user.get_full_name() # 或者 user.name，取决于 CustomUser 定义

    # 根据角色进一步细化UI上显示的角色或权限标识
    if user.is_superuser:
        refresh['ui_role'] = CustomUser.Role.ADMIN
    else:
        refresh['ui_role'] = user.role

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# =============================================================================
# 认证相关的视图 (登录、登出)
# =============================================================================

class LoginAPIView(APIView):
    """
    统一登录API视图。
    接收用户名(学号/工号/管理员名)和密码，返回JWT token和用户信息。
    """
    permission_classes = [permissions.AllowAny] # 允许任何人访问登录接口
    serializer_class = LoginSerializer # 使用您为JWT登录设计的 LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user'] # 获取已认证的 CustomUser 对象

            tokens = get_tokens_for_user(user) # 为该用户生成JWT Token

            # 构建成功响应的用户信息部分
            user_data = {
                "id": user.pk, # 或者 user.username
                "username": user.username, # CustomUser 的登录名
                "name": user.get_full_name(),
                "role": user.role, # CustomUser 中定义的角色
            }

            # 根据角色尝试附加 Profile 中的特定ID (学号/工号)
            if user.role == CustomUser.Role.STUDENT:
                try:
                    user_data['student_id_num'] = user.student_profile.student_id_num
                except CustomUser.student_profile.RelatedObjectDoesNotExist:
                    user_data['student_id_num'] = None # Profile 可能尚未创建
            elif user.role == CustomUser.Role.TEACHER:
                try:
                    user_data['teacher_id_num'] = user.teacher_profile.teacher_id_num
                except CustomUser.teacher_profile.RelatedObjectDoesNotExist:
                    user_data['teacher_id_num'] = None

            # 如果是管理员角色，前端可能需要一个明确的标识
            if user.is_superuser or user.role == CustomUser.Role.ADMIN:
                user_data['is_admin_ui'] = True


            return Response({
                "status": "success",
                "message": "登录成功",
                "tokens": tokens,
                "user": user_data
            }, status=status.HTTP_200_OK)

        # 验证失败，LoginSerializer 会抛出 ValidationError，DRF默认会处理成400
        # 为了返回统一的错误格式，可以这样：
        error_message = "用户名或密码有误"
        if serializer.errors: # 如果有具体的错误信息
            # 通常 serializer.errors 是一个字典，例如 {'non_field_errors': ['错误信息']}
            # 我们可以取第一条非字段错误
            non_field_errors = serializer.errors.get('non_field_errors')
            if non_field_errors and isinstance(non_field_errors, list) and non_field_errors:
                error_message = str(non_field_errors[0])
            else: # 如果没有非字段错误，可能是字段级错误，但也统一提示
                  # 或者你想更细致地显示 serializer.errors.get('username') 或 .get('password')
                  # 但通常登录不建议太具体
                pass


        return Response({
            "status": "error",
            "message": error_message,
            # "details": serializer.errors # 生产环境可以考虑不返回详细的details
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    登出API视图。
    对于JWT，通常是将Refresh Token加入黑名单。
    """
    permission_classes = [permissions.IsAuthenticated] # 只有登录用户才能登出

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"detail": "必须提供Refresh token。"},
                                status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist() # 将 refresh token 加入黑名单 (需要在 settings.py 中配置 'rest_framework_simplejwt.token_blacklist')

            return Response({"status": "success", "message": "已成功登出"},
                            status=status.HTTP_200_OK) # 或者 HTTP_204_NO_CONTENT
        except TokenError as e:
            # print(f"TokenError on logout: {e}") # 调试用
            return Response({"detail": "提供的Refresh token无效或已过期。"},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # print(f"Exception on logout: {e}") # 调试用
            return Response({"detail": "登出时发生错误。"},
                            status=status.HTTP_400_BAD_REQUEST)








from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model # 用于获取 AUTH_USER_MODEL
from .models import Student, Teacher # 导入你的 Student Profile 和 Teacher Profile 模型
from .serializers import ( # 确保你已经在 serializers.py 中定义了这些
    CustomUserSerializer, 
    StudentProfileSerializer, 
    TeacherProfileSerializer
)

CustomUser = get_user_model() # 获取你在 settings.py 中定义的 AUTH_USER_MODEL

class CustomUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing CustomUser accounts.
    Admins can manage all users. Regular users might have restricted access.
    """
    queryset = CustomUser.objects.all().order_by('username')
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAdminUser] # 示例：只有管理员可以访问所有用户信息
    # 根据需要调整权限，例如允许用户查看自己的信息，或创建账户等
    # 如果允许用户创建账户 (注册)，POST 方法的权限需要调整，
    # 通常注册会有单独的 API 端点，权限为 AllowAny。

class StudentProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Student profiles.
    """
    queryset = Student.objects.all().order_by('student_id_num') # 确保 Student 模型中有 student_id_num
    serializer_class = StudentProfileSerializer
    
    # 权限示例：
    # 1. 登录用户才能访问 (IsAuthenticated)
    # 2. 学生只能查看/修改自己的档案，管理员可以管理所有 (需要自定义权限)
    permission_classes = [permissions.IsAuthenticated] # 先设置为登录用户可访问
    # 后续会由负责权限的成员D来定义更细致的权限，例如：
    # from .permissions import IsOwnerOrAdminReadOnly # 假设有这样的自定义权限
    # permission_classes = [IsOwnerAdminOrReadOnly] 

    # 如果需要根据当前登录用户过滤学生档案（例如学生只能看到自己的）
    # def get_queryset(self):
    #     user = self.request.user
    #     if user.is_authenticated:
    #         if hasattr(user, 'student_profile') and user.role == CustomUser.Role.STUDENT:
    #             return Student.objects.filter(user=user)
    #         elif user.is_staff or user.role == CustomUser.Role.ADMIN: # 管理员或教职工可以查看所有
    #             return Student.objects.all().order_by('student_id_num')
    #     return Student.objects.none() # 未登录或无权限则不返回任何数据

class TeacherProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Teacher profiles.
    """
    queryset = Teacher.objects.all().order_by('teacher_id_num') # 确保 Teacher 模型中有 teacher_id_num
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated] # 先设置为登录用户可访问
    # 权限逻辑类似 StudentProfileViewSet，后续由成员D细化
    # from .permissions import IsOwnerOrAdminReadOnly
    # permission_classes = [IsOwnerAdminOrReadOnly]

    # 也可以添加 get_queryset 逻辑，例如教师只能看到自己的档案，管理员可以查看所有
    # def get_queryset(self):
    #     user = self.request.user
    #     if user.is_authenticated:
    #         if hasattr(user, 'teacher_profile') and user.role == CustomUser.Role.TEACHER:
    #             return Teacher.objects.filter(user=user)
    #         elif user.is_staff or user.role == CustomUser.Role.ADMIN:
    #             return Teacher.objects.all().order_by('teacher_id_num')
    #     return Teacher.objects.none()

# -----------------------------------------------------------------------------
# 认证相关的视图 (登录、登出、注册等)
# -----------------------------------------------------------------------------
# 强烈推荐使用 dj_rest_auth 或 djoser 这样的包来处理认证 API。
# 如果手动实现，会类似下面这样，但会更复杂：

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.contrib.auth import authenticate, login, logout
# from .serializers import LoginSerializer # 你需要创建一个 LoginSerializer

# class LoginAPIView(APIView):
#     permission_classes = [permissions.AllowAny] # 允许任何人访问登录接口
#     serializer_class = LoginSerializer # 你需要定义这个

#     def post(self, request, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             username = serializer.validated_data.get('username') # 或者你 CustomUser 的 USERNAME_FIELD
#             password = serializer.validated_data.get('password')
#             user = authenticate(request, username=username, password=password)
#             if user:
#                 if user.is_active:
#                     login(request, user) # 创建 session
#                     # 如果使用 Token 认证，这里会生成并返回 Token
#                     # from rest_framework.authtoken.models import Token
#                     # token, created = Token.objects.get_or_create(user=user)
#                     # return Response({'token': token.key, 'user_id': user.pk, 'role': user.role }, status=status.HTTP_200_OK)
#                     return Response({'message': '登录成功', 'user_id': user.pk, 'role': user.role, 'username': user.username }, status=status.HTTP_200_OK)
#                 else:
#                     return Response({'error': '用户账户已被禁用'}, status=status.HTTP_403_FORBIDDEN)
#             else:
#                 return Response({'error': '用户名或密码错误'}, status=status.HTTP_400_BAD_REQUEST)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class LogoutAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated] # 只有登录用户才能登出

#     def post(self, request, *args, **kwargs):
#         # 如果使用 Token 认证，需要删除 Token
#         # request.user.auth_token.delete()
#         logout(request) # 删除 session
#         return Response({'message': '登出成功'}, status=status.HTTP_200_OK)

# 你可能还需要注册视图、密码修改视图等。





from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser # 导入您的 CustomUser 模型

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    # 在token的payload中添加自定义声明 (claims)，例如用户的角色
    # 这样前端拿到access token后，可以直接解码获取角色信息，无需再次请求
    refresh['role'] = user.role # 直接从 CustomUser 获取角色
    # refresh['name'] = user.get_full_name() # 可以添加姓名等

    # 如果需要区分管理员角色 (即使 role 是 TEACHER 或 STUDENT，但他们可能是is_superuser)
    if user.is_superuser:
        refresh['actual_role_for_ui'] = CustomUser.Role.ADMIN
    else:
        refresh['actual_role_for_ui'] = user.role

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }