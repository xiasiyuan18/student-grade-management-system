# student-grade-management-system/users/tests.py

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import CustomUser, Student, Teacher
from departments.models import Department, Major
from decimal import Decimal

# 在这里创建你的测试。

class StudentProfileAPITests(APITestCase):
    """
    StudentProfileViewSet API 端点的测试套件。
    """
    @classmethod
    def setUpTestData(cls):
        # 为学生档案创建院系和专业
        cls.department = Department.objects.create(dept_code="CS", dept_name="计算机科学")
        cls.major = Major.objects.create(
            major_name="软件工程",
            department=cls.department,
            bachelor_credits_required=Decimal('150.0')
        )

        # 创建不同角色的用户
        cls.admin_user = CustomUser.objects.create_superuser(
            username='admin_user', password='password123', role=CustomUser.Role.ADMIN
        )
        cls.teacher_user = CustomUser.objects.create_user(
            username='teacher_user', password='password123', role=CustomUser.Role.TEACHER
        )
        cls.student_user1 = CustomUser.objects.create_user(
            username='student1', password='password123', role=CustomUser.Role.STUDENT
        )
        cls.student_user2 = CustomUser.objects.create_user(
            username='student2', password='password123', role=CustomUser.Role.STUDENT
        )

        # 创建相应的个人档案
        cls.student_profile1 = Student.objects.create(
            user=cls.student_user1,
            student_id_num='S00001',
            name='爱丽丝',
            id_card='111111111111111111',
            gender='女',
            department=cls.department,
            major=cls.major,
            degree_level='本科'
        )
        cls.student_profile2 = Student.objects.create(
            user=cls.student_user2,
            student_id_num='S00002',
            name='鲍勃',
            id_card='222222222222222222',
            gender='男',
            department=cls.department,
            major=cls.major,
            degree_level='本科'
        )
        
        # StudentProfileViewSet 的 URL
        cls.list_url = reverse('studentprofile-list')
        cls.detail_url = lambda pk: reverse('studentprofile-detail', kwargs={'pk': pk})

    def test_anonymous_user_cannot_access_student_profiles(self):
        """确保未经身份验证的用户无法访问任何学生档案端点。"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.get(self.detail_url(self.student_profile1.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_can_retrieve_own_profile(self):
        """确保学生可以查看自己的档案，但不能查看他人的档案。"""
        self.client.force_authenticate(user=self.student_user1)
        
        # 可以查看自己的档案
        response = self.client.get(self.detail_url(self.student_profile1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student_id_num'], 'S00001')

        # 不能查看其他学生的档案
        response = self.client.get(self.detail_url(self.student_profile2.pk))
        # 这将导致 404，因为 get_queryset 将其过滤掉了
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_cannot_list_all_profiles(self):
        """确保学生无权列出所有学生档案。"""
        self.client.force_authenticate(user=self.student_user1)
        response = self.client.get(self.list_url)
        # 权限检查会拒绝学生访问，所以我们期望收到 403 Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_and_teacher_can_list_all_profiles(self):
        """确保管理员和教师可以列出所有学生档案。"""
        # 使用管理员用户测试
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.client.logout()

        # 使用教师用户测试
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_student_can_update_own_profile_with_limited_fields(self):
        """确保学生可以使用有限的字段更新自己的档案。"""
        self.client.force_authenticate(user=self.student_user1)
        update_data = {
            'phone': '123-456-7890',
            'home_address': '主街123号'
        }
        response = self.client.patch(self.detail_url(self.student_profile1.pk), data=update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_profile1.refresh_from_db()
        self.assertEqual(self.student_profile1.phone, '123-456-7890')
        
        # 测试敏感字段不能被更新
        sensitive_update_data = {
            'student_id_num': 'S99999',  # 不在 StudentProfileSelfUpdateSerializer 中
            'credits_earned': '100.0'   # 不在 StudentProfileSelfUpdateSerializer 中
        }
        response = self.client.patch(self.detail_url(self.student_profile1.pk), data=sensitive_update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # 请求本身是有效的
        self.student_profile1.refresh_from_db()
        self.assertNotEqual(self.student_profile1.student_id_num, 'S99999') # 确认值没有被改变
        self.assertNotEqual(self.student_profile1.credits_earned, Decimal('100.0'))

    def test_student_cannot_update_another_profile(self):
        """确保学生不能更新其他学生的档案。"""
        self.client.force_authenticate(user=self.student_user1)
        update_data = {'phone': '999-999-9999'}
        response = self.client.patch(self.detail_url(self.student_profile2.pk), data=update_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # 被 get_queryset 过滤

    def test_admin_can_update_any_profile(self):
        """确保管理员可以更新任何学生的档案。"""
        self.client.force_authenticate(user=self.admin_user)
        update_data = {
            'credits_earned': '50.5'
        }
        response = self.client.patch(self.detail_url(self.student_profile1.pk), data=update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_profile1.refresh_from_db()
        self.assertEqual(self.student_profile1.credits_earned, Decimal('50.5'))

    def test_student_or_teacher_cannot_create_or_delete_profile(self):
        """确保非管理员用户不能创建或删除学生档案。"""
        # 测试学生用户
        self.client.force_authenticate(user=self.student_user1)
        response = self.client.post(self.list_url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(self.detail_url(self.student_profile2.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # IsAdminRole 权限检查
        self.client.logout()

        # 测试教师用户
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.post(self.list_url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(self.detail_url(self.student_profile2.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)