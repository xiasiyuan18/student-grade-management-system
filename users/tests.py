from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from users.models import CustomUser, Teacher, Student
from departments.models import Department, Major
from courses.models import Course, TeachingAssignment
from grades.models import Grade

class TeacherGradeUpdateTest(APITestCase):

    def setUp(self):
        # 创建院系和专业
        self.department = Department.objects.create(dept_code="CS", dept_name="计算机科学")
        self.major = Major.objects.create(major_name="软件工程", department=self.department)

        # 创建教师
        self.teacher_user = CustomUser.objects.create_user(
            username='prof_wong', password='password123', role=CustomUser.Role.TEACHER
        )
        self.teacher_profile = Teacher.objects.create(
            user=self.teacher_user, teacher_id_num='T888', name='王老师', department=self.department
        )

        # 创建学生
        self.student_user = CustomUser.objects.create_user(
            username='stu_li', password='password123', role=CustomUser.Role.STUDENT
        )
        self.student_profile = Student.objects.create(
            user=self.student_user, student_id_num='S12345', name='小李', id_card='111222333444555666', 
            gender='男', major=self.major, department=self.department, degree_level='本科'
        )

        # 创建课程
        self.course = Course.objects.create(
            course_id='CS101', course_name='计算机导论', credits=Decimal('3.0'), department=self.department
        )

        # 创建授课安排
        self.teaching_assignment = TeachingAssignment.objects.create(
            teacher=self.teacher_profile, course=self.course, semester='2024 Fall'
        )

        # 创建初始成绩
        self.grade = Grade.objects.create(
            student=self.student_profile,
            teaching_assignment=self.teaching_assignment,
            score=Decimal('80.0')
        )

    def test_teacher_can_update_grade_for_own_student(self):
        self.client.force_authenticate(user=self.teacher_user)

        update_data = {
            'student_id': self.student_profile.pk,
            'score': '92.5'
        }

        url = reverse('student-grade-for-teaching-assignment-detail', kwargs={
            'teaching_assignment_id': self.teaching_assignment.pk,
            'student_id': self.student_profile.pk
        })

        response = self.client.put(url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['score']), Decimal('92.50'))

        # 验证数据库更新
        self.grade.refresh_from_db()
        self.assertEqual(self.grade.score, Decimal('92.50'))