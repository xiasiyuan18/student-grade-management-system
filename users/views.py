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