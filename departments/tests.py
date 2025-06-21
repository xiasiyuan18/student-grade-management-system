from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Department, Major
from users.models import CustomUser
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Department, Major

CustomUser = get_user_model()

class DepartmentAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # 创建不同角色的用户
        cls.admin_user = CustomUser.objects.create_superuser(
            username='admin_dept_test', 
            password='password123',
            email='admin_dept@example.com',
            role=CustomUser.Role.ADMIN
        )
        cls.student_user = CustomUser.objects.create_user(
            username='student_dept_test', 
            password='password123',
            email='student_dept@example.com',
            role=CustomUser.Role.STUDENT
        )

        # 创建一些初始数据用于测试 GET, PUT, DELETE
        cls.department1 = Department.objects.create(dept_code="CS", dept_name="计算机科学与技术")
        cls.department2 = Department.objects.create(dept_code="MATH", dept_name="数学系")

        cls.list_url = reverse('departments:department-list')
        cls.detail_url = lambda pk: reverse('departments:department-detail', kwargs={'pk': pk})

    def test_list_departments_anonymous_user_forbidden(self):
        """测试匿名用户无法访问院系列表 (如果权限设置为 IsAuthenticated 或更高)"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_departments_authenticated_student_allowed_read_only(self):
        """测试学生用户可以读取院系列表"""
        self.client.force_authenticate(user=self.student_user) 
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2) # 期望返回两个院系
        self.client.logout()

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
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
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
        response = self.client.patch(self.detail_url(self.department1.pk), updated_data, format='json') 
        
        if response.status_code != status.HTTP_200_OK:
            print("Update Department Fail Response Data:", response.data) 
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.department1.refresh_from_db()
        self.assertEqual(self.department1.dept_name, '计算机科学与工程')
        self.client.logout()

    def test_delete_department_admin_user_success(self):
        """测试管理员可以删除院系 (假设没有被 Major PROTECT)"""
        temp_dept = Department.objects.create(dept_code="TEMP", dept_name="临时院系")
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url(temp_dept.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Department.objects.filter(pk=temp_dept.pk).exists())
        self.client.logout()

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
        cls.list_url = reverse('departments:major-list')
        cls.detail_url = lambda pk: reverse('departments:major-detail', kwargs={'pk': pk})

    
    def test_list_majors_authenticated_user(self):
        """测试登录用户可以查看专业列表"""
        url_to_test = self.list_url 
        
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(url_to_test)

        self.assertEqual(
            response.status_code, 
            status.HTTP_200_OK,
            f"请求 {url_to_test} 失败，期望状态码 200，实际为 {response.status_code}，"
            f"响应内容: {response.content.decode()}" 
        )

    def test_create_major_admin_user_success(self):
        """测试管理员可以创建专业"""
        print(f"Generated URL for major create (POST): {self.list_url}")
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