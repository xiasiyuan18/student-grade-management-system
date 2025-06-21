from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.utils import IntegrityError as DjangoIntegrityError

from users.models import CustomUser, Student, Teacher 
from departments.models import Department 
from departments.models import Major 
from courses.models import Course, TeachingAssignment 

from grades.models import Grade
from grades.services import calculate_and_update_student_credits, create_or_update_grade

User = get_user_model()


class GradeModelTest(TestCase):
    """测试Grade模型及GPA计算和验证"""
    def setUp(self):
        self.department = Department.objects.create(dept_code="CS", dept_name="计算机科学与技术系")
        self.major = Major.objects.create(major_name="软件工程", department=self.department, bachelor_credits_required=Decimal('120.0')) 

        self.student_user = User.objects.create_user(
            username='studentuser',
            password='password123',
            role=CustomUser.Role.STUDENT
        )
        self.student_profile = Student.objects.create(
            user=self.student_user,
            student_id_num='S12345', 
            name='张三',
            id_card='123456789012345678',
            gender='男',
            major=self.major,
            department=self.department,
            degree_level='本科'
        )

        self.teacher_user = User.objects.create_user(
            username='teacheruser', 
            password='password123',
            role=CustomUser.Role.TEACHER, 
            is_staff=True 
        )
        self.teacher_profile = Teacher.objects.create(
            user=self.teacher_user, 
            teacher_id_num='T001', 
            name='李四',
            department=self.department
        )
        
        self.admin_user = User.objects.create_superuser(
            username='admin', password='adminpassword', role=CustomUser.Role.ADMIN
        )

        self.course = Course.objects.create(course_id='CS101', course_name='计算机导论', credits=Decimal('3.0'), department=self.department)
        self.teaching_assignment = TeachingAssignment.objects.create(teacher=self.teacher_profile, course=self.course, semester='2023-2024-1')

    def test_grade_creation_and_gpa_calculation(self):
        """测试成绩创建和GPA自动计算"""
        grade = Grade.objects.create(
            student=self.student_profile,
            teaching_assignment=self.teaching_assignment,
            score=Decimal('85.5')
        )
        self.assertEqual(grade.score, Decimal('85.5'))
        self.assertEqual(grade.gpa, Decimal('3.7'))

        # 测试不同分数的GPA计算
        grade_a_ta = TeachingAssignment.objects.create(teacher=self.teacher_profile, course=self.course, semester='2023-2024-2')
        grade_a = Grade.objects.create(student=self.student_profile, teaching_assignment=grade_a_ta, score=Decimal('90.0'))
        self.assertEqual(grade_a.gpa, Decimal('4.0'))
        
        grade_b_ta = TeachingAssignment.objects.create(teacher=self.teacher_profile, course=self.course, semester='2024-2025-1')
        grade_b = Grade.objects.create(student=self.student_profile, teaching_assignment=grade_b_ta, score=Decimal('59.9'))
        self.assertEqual(grade_b.gpa, Decimal('0.0'))

    def test_grade_unique_together(self):
        """测试唯一性约束"""
        Grade.objects.create(student=self.student_profile, teaching_assignment=self.teaching_assignment, score=Decimal('80.0'))
        
        from django.db.utils import IntegrityError
        with self.assertRaises(IntegrityError): 
            Grade.objects.create(student=self.student_profile, teaching_assignment=self.teaching_assignment, score=Decimal('90.0'))

class GradeAPITest(TestCase):
    """测试Grade API端点和权限"""
    def setUp(self):
        self.client = APIClient()
        self.department = Department.objects.create(dept_code="MATH", dept_name="数学系")
        self.major = Major.objects.create(major_name="应用数学", department=self.department, bachelor_credits_required=Decimal('120.0')) 

        self.admin_user = User.objects.create_superuser(
            username='admin', password='adminpassword', role=CustomUser.Role.ADMIN
        )
        self.student_user = User.objects.create_user(
            username='studentuser', password='password123', role=CustomUser.Role.STUDENT
        )
        self.student_profile = Student.objects.create(
            user=self.student_user, student_id_num='S12345', name='张三', 
            id_card='123456789012345678', gender='男', major=self.major, department=self.department, degree_level='本科'
        )
        self.teacher_user = User.objects.create_user(
            username='teacheruser', password='password123', role=CustomUser.Role.TEACHER, is_staff=True
        )
        self.teacher_profile = Teacher.objects.create(
            user=self.teacher_user, teacher_id_num='T001', name='李四', department=self.department
        )
        
        self.other_student_user = User.objects.create_user(username='other_student', password='password123', role=CustomUser.Role.STUDENT)
        self.other_student_profile = Student.objects.create(
            user=self.other_student_user, student_id_num='S99999', name='王五', 
            id_card='999999999999999999', gender='男', major=self.major, department=self.department, degree_level='本科'
        )
        self.other_teacher_user = User.objects.create_user(username='other_teacher', password='password123', role=CustomUser.Role.TEACHER, is_staff=True)
        self.other_teacher_profile = Teacher.objects.create(
            user=self.other_teacher_user, teacher_id_num='T999', name='赵六', department=self.department
        )

        self.course_cs = Course.objects.create(course_id='CS101', course_name='计算机导论', credits=Decimal('3.0'), department=self.department)
        self.course_math = Course.objects.create(course_id='MA101', course_name='高等数学', credits=Decimal('4.0'), department=self.department)

        self.teaching_cs = TeachingAssignment.objects.create(teacher=self.teacher_profile, course=self.course_cs, semester='2023-2024-1')
        self.teaching_math_other = TeachingAssignment.objects.create(teacher=self.other_teacher_profile, course=self.course_math, semester="2025 Spring")

        self.grade_student_cs = Grade.objects.create(student=self.student_profile, teaching_assignment=self.teaching_cs, score=Decimal('85.0'))
        self.grade_other_student_cs = Grade.objects.create(student=self.other_student_profile, teaching_assignment=self.teaching_cs, score=Decimal('90.0'))
        self.grade_student_math_other_teacher = Grade.objects.create(student=self.student_profile, teaching_assignment=self.teaching_math_other, score=Decimal('75.0'))

    def test_unauthenticated_cannot_access_grades(self):
        """未认证用户无法访问成绩API"""
        response = self.client.get(reverse('teaching-assignment-grades-list', kwargs={'teaching_assignment_id': self.teaching_cs.pk}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.put(reverse('student-grade-for-teaching-assignment-detail', 
                                          kwargs={'teaching_assignment_id': self.teaching_cs.pk, 'student_id': self.student_profile.pk}), 
                                   {'score': '10'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_can_list_own_grades(self):
        """学生只能列出自己的成绩"""
        self.client.force_authenticate(user=self.student_user) 
        response = self.client.get(reverse('teaching-assignment-grades-list', kwargs={'teaching_assignment_id': self.teaching_cs.pk}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_create_grade(self):
        """学生不能创建成绩"""
        self.client.force_authenticate(user=self.student_user)
        data = {
            'student_id': self.student_profile.pk,
            'score': 90.0
        }
        url = reverse('student-grade-for-teaching-assignment-detail', kwargs={
            'teaching_assignment_id': self.teaching_cs.pk,
            'student_id': self.student_profile.pk 
        })
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_access_own_teaching_assignment_grades(self):
        """教师可以访问自己授课的成绩"""
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.get(reverse('teaching-assignment-grades-list', kwargs={'teaching_assignment_id': self.teaching_cs.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_teacher_cannot_access_other_teacher_grades(self):
        """教师不能访问其他教师的成绩"""
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.get(reverse('teaching-assignment-grades-list', kwargs={'teaching_assignment_id': self.teaching_math_other.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_teacher_can_update_own_student_grade(self):
        """教师可以修改自己授课学生的成绩"""
        self.client.force_authenticate(user=self.teacher_user)
        data = {'student_id': self.student_profile.pk, 'score': '95.0'}
        url = reverse('student-grade-for-teaching-assignment-detail', kwargs={
            'teaching_assignment_id': self.teaching_cs.pk,
            'student_id': self.student_profile.pk
        })
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['score']), Decimal('95.0'))

    def test_admin_can_access_all_grades(self):
        """管理员可以访问所有成绩"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('teaching-assignment-grades-list', kwargs={'teaching_assignment_id': self.teaching_cs.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
