from django.test import TestCase

# Create your tests here.
from django.urls import reverse # 用于反向解析 URL 名称
from rest_framework import status
from rest_framework.test import APITestCase # DRF 提供的测试基类
from django.contrib.auth import get_user_model # 获取你的 CustomUser 模型
from .models import Department, Major # 导入你的模型
from users.models import CustomUser # 或者直接导入 CustomUser，如果 get_user_model() 不方便
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Department, Major

CustomUser = get_user_model()

class DepartmentAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # 创建不同角色的用户，为测试权限做准备
        cls.admin_user = CustomUser.objects.create_superuser(
            username='admin_dept_test', 
            password='password123',
            email='admin_dept@example.com',
            role=CustomUser.Role.ADMIN # 假设 CustomUser 有 role 字段
        )
        cls.student_user = CustomUser.objects.create_user(
            username='student_dept_test', 
            password='password123',
            email='student_dept@example.com',
            role=CustomUser.Role.STUDENT
        )
        # (可以再创建一个 Teacher 用户)

        # 创建一些初始数据用于测试 GET, PUT, DELETE
        cls.department1 = Department.objects.create(dept_code="CS", dept_name="计算机科学与技术")
        cls.department2 = Department.objects.create(dept_code="MATH", dept_name="数学系")

        # URL 名称，假设你在 departments/urls.py 中为 DepartmentViewSet 设置了 basename='department'
        cls.list_url = reverse('departments:department-list') # 假设 app_name='departments'
        cls.detail_url = lambda pk: reverse('departments:department-detail', kwargs={'pk': pk})

    def test_list_departments_anonymous_user_forbidden(self):
        """测试匿名用户无法访问院系列表 (如果权限设置为 IsAuthenticated 或更高)"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # 或 403，取决于你的默认认证

    def test_list_departments_authenticated_student_allowed_read_only(self):
        """测试学生用户可以读取院系列表 (假设权限是 IsAdminOrReadOnly 或类似)"""
        self.client.force_authenticate(user=self.student_user) # 强制认证为学生用户
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # 假设分页关闭或这是第一页
        self.client.logout() # 登出

    def test_create_department_admin_user_success(self):
        """测试管理员用户可以创建院系"""
        self.client.force_authenticate(user=self.admin_user)
        data = {'dept_code': 'EE', 'dept_name': '电子工程系'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Department.objects.filter(dept_code='EE').exists())
        self.client.logout()

    def test_create_department_student_user_forbidden(self):
        """测试学生用户不能创建院系"""
        self.client.force_authenticate(user=self.student_user)
        data = {'dept_code': 'PHY', 'dept_name': '物理系'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # 假设权限是 IsAdminOrReadOnly
        self.client.logout()

    def test_retrieve_department_success(self):
        """测试可以获取单个院系详情"""
        self.client.force_authenticate(user=self.student_user) # 学生也可以查看
        response = self.client.get(self.detail_url(self.department1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dept_code'], self.department1.dept_code)
        self.client.logout()

    def test_update_department_admin_user_success(self):
        """测试管理员可以更新院系"""
        self.client.force_authenticate(user=self.admin_user)
        updated_data = {'dept_name': '计算机科学与工程'}
        # 使用 PATCH 进行部分更新，并指定 format='json' (如果你的数据是json格式)
        response = self.client.patch(self.detail_url(self.department1.pk), updated_data, format='json') 
        
        # 调试：打印响应数据，看看具体错误是什么
        if response.status_code != status.HTTP_200_OK:
            print("Update Department Fail Response Data:", response.data) 
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.department1.refresh_from_db()
        self.assertEqual(self.department1.dept_name, '计算机科学与工程')
        self.client.logout()

    def test_delete_department_admin_user_success(self):
        """测试管理员可以删除院系 (假设没有被 Major PROTECT)"""
        # 注意：如果 Major 表中有数据关联到这个 Department，并且 on_delete=models.PROTECT，则删除会失败
        # 你可能需要先创建一个没有 Major 关联的 Department 来测试纯粹的删除，或者测试 PROTECT 行为
        temp_dept = Department.objects.create(dept_code="TEMP", dept_name="临时院系")
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url(temp_dept.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Department.objects.filter(pk=temp_dept.pk).exists())
        self.client.logout()

    # ... 更多测试用例，例如测试字段验证、搜索、筛选、分页等 ...


class MajorAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = CustomUser.objects.create_superuser(
            username='admin_major_test', password='password123', email='admin_major@example.com', role=CustomUser.Role.ADMIN
        )
        cls.student_user = CustomUser.objects.create_user(
            username='student_major_test', password='password123', email='student_major@example.com', role=CustomUser.Role.STUDENT
        )
        cls.department_cs = Department.objects.create(dept_code="CS_TEST", dept_name="测试计算机系")
        cls.major1 = Major.objects.create(
            major_name="软件工程", 
            department=cls.department_cs, 
            bachelor_credits_required=160
        )
        cls.list_url = reverse('departments:major-list') # 假设 app_name='departments', basename='major'
        cls.detail_url = lambda pk: reverse('departments:major-detail', kwargs={'pk': pk})

    def test_list_majors_authenticated_user(self):
        """测试登录用户可以查看专业列表"""
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # ... 更多断言 ...
        self.client.logout()

    def test_create_major_admin_user_success(self):
        """测试管理员可以创建专业"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'major_name': '网络工程',
            'department': self.department_cs.pk, # 发送外键的 ID
            'bachelor_credits_required': 150.0
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Major.objects.filter(major_name='网络工程').exists())
        self.client.logout()
    
    # ... 更多针对 Major 的 CRUD 和权限测试用例 ...