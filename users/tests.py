# student-grade-management-system/users/tests.py

# 这段代码可以放在一个新的测试文件或 grades/tests.py 中
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

# 导入所有需要的模型
from users.models import CustomUser, Teacher, Student
from departments.models import Department, Major
from courses.models import Course, TeachingAssignment
from grades.models import Grade

class TeacherGradeUpdateTest(APITestCase):

    def setUp(self):
        """为测试准备所有必需的实体"""
        # 1. 创建基础的院系和专业
        self.department = Department.objects.create(dept_code="CS", dept_name="计算机科学")
        self.major = Major.objects.create(major_name="软件工程", department=self.department)

        # 2. 创建一个教师用户及其档案
        self.teacher_user = CustomUser.objects.create_user(
            username='prof_wong', password='password123', role=CustomUser.Role.TEACHER
        )
        self.teacher_profile = Teacher.objects.create(
            user=self.teacher_user, teacher_id_num='T888', name='王老师', department=self.department
        )

        # 3. 创建一个学生用户及其档案
        self.student_user = CustomUser.objects.create_user(
            username='stu_li', password='password123', role=CustomUser.Role.STUDENT
        )
        self.student_profile = Student.objects.create(
            user=self.student_user, student_id_num='S12345', name='小李', id_card='111222333444555666', 
            gender='男', major=self.major, department=self.department, degree_level='本科'
        )

        # 4. 创建一门课程
        self.course = Course.objects.create(
            course_id='CS101', course_name='计算机导论', credits=Decimal('3.0'), department=self.department
        )

        # 5. 创建一个授课安排，将【王老师】和【计算机导论】关联起来
        self.teaching_assignment = TeachingAssignment.objects.create(
            teacher=self.teacher_profile, course=self.course, semester='2024 Fall'
        )

        # 6. 为【小李】在这门课上创建一个初始成绩
        self.grade = Grade.objects.create(
            student=self.student_profile,
            teaching_assignment=self.teaching_assignment,
            score=Decimal('80.0') # 初始分数为80
        )
        # 续上一个代码块，在 TeacherGradeUpdateTest 类中添加此方法
    def test_teacher_can_update_grade_for_own_student(self):
        """
        测试场景：教师成功更新自己所教学生的成绩
        """
        # 1. 关键：模拟【王老师】登录
        self.client.force_authenticate(user=self.teacher_user)

        # 2. 准备要发送的更新数据。成绩可以是一个字符串形式的数字。
        update_data = {
            'student_id': self.student_profile.pk,  # <--- 添加这一行
            'score': '92.5'
        }

        # 3. 获取要请求的 API URL
        # 这个 URL 对应 grades/urls.py 中的 'student-grade-for-teaching-assignment-detail'
        # 需要传入授课安排的ID和学生的ID
        url = reverse('student-grade-for-teaching-assignment-detail', kwargs={
            'teaching_assignment_id': self.teaching_assignment.pk,
            'student_id': self.student_profile.pk
        })

        # 4. 使用 PUT 方法发送请求来更新成绩
        response = self.client.put(url, update_data, format='json')

        # 5. 断言请求是否成功 (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 6. 断言返回的数据中，分数是否已更新
        self.assertEqual(Decimal(response.data['score']), Decimal('92.50'))

        # 7. (推荐) 从数据库中重新获取成绩对象，再次确认数据已被持久化
        self.grade.refresh_from_db()
        self.assertEqual(self.grade.score, Decimal('92.50'))