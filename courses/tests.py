
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from decimal import Decimal


from users.models import CustomUser, Teacher, Student 
from departments.models import Department 
from departments.models import Major 
from .models import Course, TeachingAssignment 


User = get_user_model() 

class CourseModelTest(TestCase):
    """测试Course模型"""
    def setUp(self):
        self.department = Department.objects.create(dept_code="CS", dept_name="计算机科学与技术系")
        self.major = Major.objects.create(major_name="软件工程", department=self.department, bachelor_credits_required=Decimal('120.0')) 
        
        self.student_user = User.objects.create_user(username='test_student', password='password123', role=CustomUser.Role.STUDENT)
        self.student_profile = Student.objects.create(user=self.student_user, student_id_num='S00001', name='测试学生', id_card='000000000000000001', gender='男', major=self.major, department=self.department, degree_level='本科') 

        self.teacher_user = User.objects.create_user(username='test_teacher', password='password123', role=CustomUser.Role.TEACHER, is_staff=False) # 修正 is_staff=False
        self.teacher_profile = Teacher.objects.create(user=self.teacher_user, teacher_id_num='T001', name='测试教师', department=self.department)

        self.course = Course.objects.create(course_id='CS101', course_name='计算机导论', credits=Decimal('3.0'), department=self.department)

    def test_teaching_assignment_creation(self): 
        """测试教师授课记录是否能成功创建并关联"""
        course = Course.objects.create(course_id='CS102', course_name='数据结构', credits=Decimal('4.0'), department=self.department)
        teaching_assignment = TeachingAssignment.objects.create(teacher=self.teacher_profile, course=course, semester='2023 Fall')
        
        self.assertEqual(teaching_assignment.teacher, self.teacher_profile)
        self.assertEqual(teaching_assignment.course, course)
        self.assertEqual(teaching_assignment.semester, '2023 Fall')
        with self.assertRaises(Exception): # Django IntegrityError
            TeachingAssignment.objects.create(teacher=self.teacher_profile, course=course, semester='2023 Fall')

class CourseAPITest(TestCase):
    """测试Course和TeachingAssignment的API"""
    def setUp(self):
        self.client = APIClient()
        self.department = Department.objects.create(dept_code="MATH", dept_name="数学系")
        self.major = Major.objects.create(major_name="应用数学", department=self.department, bachelor_credits_required=Decimal('120.0')) 

        self.admin_user = User.objects.create_superuser(username='admin', password='adminpassword', role=CustomUser.Role.ADMIN)
        
        self.teacher_user = User.objects.create_user(username='teacher1', password='password123', role=CustomUser.Role.TEACHER, is_staff=False) # 修正 is_staff=False
        self.teacher_profile = Teacher.objects.create(user=self.teacher_user, teacher_id_num='T002', name='教师一', department=self.department)
        
        self.course1 = Course.objects.create(course_id='MATH101', course_name='高等数学', credits=Decimal('4.0'), department=self.department)
        self.teaching1 = TeachingAssignment.objects.create(teacher=self.teacher_profile, course=self.course1, semester='2023-2024-1')

        self.student_user = User.objects.create_user(username='studentuser', password='password123', role=CustomUser.Role.STUDENT)
        self.student_profile = Student.objects.create(user=self.student_user, student_id_num='S12345', name='张三', id_card='123456789012345678', gender='男', major=self.major, department=self.department, degree_level='本科') 


    def test_unauthenticated_cannot_access_courses(self):
        """未认证用户无法访问课程API"""
        response = self.client.get(reverse('course-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(reverse('course-list'), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_can_list_courses(self):
        """认证用户可以列出课程"""
        self.client.force_authenticate(user=self.teacher_user) 
        response = self.client.get(reverse('course-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 修正断言以适应分页 (response.data 是字典，包含 'results' 键)
        self.assertEqual(len(response.data['results']), 1) 

    def test_admin_can_create_course(self):
        """管理员可以创建课程"""
        self.client.force_authenticate(user=self.admin_user)
        data = {'course_id': 'PHS101', 'course_name': '普通物理', 'credits': '3.5', 'department': self.department.id}
        response = self.client.post(reverse('course-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 2)

    def test_teacher_cannot_create_course(self):
        """普通教师不能创建课程 (基于 IsAdminOrReadOnly 权限)"""
        self.client.force_authenticate(user=self.teacher_user)
        data = {'course_id': 'CHEM201', 'course_name': '有机化学', 'credits': '3.0', 'department': self.department.id}
        response = self.client.post(reverse('course-list'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 


    def test_admin_can_delete_teaching_assignment(self):
        """管理员可以删除教师授课记录"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(reverse('teachingassignment-detail', kwargs={'pk': self.teaching1.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TeachingAssignment.objects.count(), 0)