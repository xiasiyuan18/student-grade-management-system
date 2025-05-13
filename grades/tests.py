# grades/tests.py (续)
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
from courses.models import Course, TeachingAssignment
from .models import Grade
from .services import calculate_and_update_student_credits # 假设这个服务函数存在
from rest_framework.test import APIClient
from users.models import Department, CustomUser, Teacher, Student


class GradeAPITests(APITestCase): # APITestCase 会为每个测试方法重置数据库
    def setUp(self):
        # 与 GradeServiceTests 类似的 setUp，创建用户、课程、TA等
        self.department = Department.objects.create(dept_code="CS", dept_name="Computer Science")
        self.teacher_user = CustomUser.objects.create_user(username="api_teacher", password="password", role=CustomUser.Role.TEACHER)
        self.teacher_profile = Teacher.objects.create(user=self.teacher_user, teacher_id_num="TAPI001", name="API Prof", department=self.department)
        self.student_user = CustomUser.objects.create_user(username="api_student", password="password", role=CustomUser.Role.STUDENT)
        self.student_profile = Student.objects.create(user=self.student_user, student_id_num="SAPI001", name="API Student", department=self.department)
        self.course = Course.objects.create(course_id="API101", course_name="API Course", credits=Decimal("3.0"), department=self.department)
        self.teaching_assignment = TeachingAssignment.objects.create(teacher=self.teacher_profile, course=self.course, semester="2025 Spring")

        self.client = APIClient() # APITestCase 自带 self.client
        self.client.force_authenticate(user=self.teacher_user) # 以教师身份登录

        # URL for StudentGradeForTeachingAssignmentView
        self.grade_detail_url = reverse(
            'student-grade-for-teaching-assignment-detail',
            kwargs={'teaching_assignment_id': self.teaching_assignment.pk, 'student_id': self.student_profile.user_id} # 注意 student_id 应该是 Student Profile 的 user_id (PK)
        )
        # URL for TeachingAssignmentGradesListView
        self.grade_list_url = reverse(
            'teaching-assignment-grades-list',
            kwargs={'teaching_assignment_id': self.teaching_assignment.pk}
        )

    def test_teacher_can_create_grade_via_put(self):
        payload = {'score': '92.50'}
        response = self.client.put(self.grade_detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED) # 如果你区分创建和更新
        self.assertTrue(Grade.objects.filter(student=self.student_profile, teaching_assignment=self.teaching_assignment).exists())
        grade = Grade.objects.get(student=self.student_profile, teaching_assignment=self.teaching_assignment)
        self.assertEqual(grade.score, Decimal('92.50'))
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.credits_earned, self.course.credits)

    def test_teacher_can_update_grade_via_put(self):
        # 先创建一条成绩
        Grade.objects.create(student=self.student_profile, teaching_assignment=self.teaching_assignment, score=Decimal('70.00'), last_modified_by=self.teacher_user)
        calculate_and_update_student_credits(self.student_profile) # 手动触发一下学分计算
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.credits_earned, self.course.credits)

        payload = {'score': '88.00'}
        response = self.client.put(self.grade_detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        grade = Grade.objects.get(student=self.student_profile, teaching_assignment=self.teaching_assignment)
        self.assertEqual(grade.score, Decimal('88.00'))
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.credits_earned, self.course.credits) # 学分通常不变，除非课程学分变了

    def test_teacher_can_clear_grade_via_put(self):
        Grade.objects.create(student=self.student_profile, teaching_assignment=self.teaching_assignment, score=Decimal('90.00'), last_modified_by=self.teacher_user)
        calculate_and_update_student_credits(self.student_profile)

        payload = {'score': ''} # 或者 None，取决于 GradeUpdateSerializer 如何处理
        response = self.client.put(self.grade_detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        grade = Grade.objects.get(student=self.student_profile, teaching_assignment=self.teaching_assignment)
        self.assertIsNone(grade.score)
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.credits_earned, Decimal('0.00'))

    def test_teacher_get_grades_for_their_teaching_assignment(self):
        Grade.objects.create(student=self.student_profile, teaching_assignment=self.teaching_assignment, score=Decimal('85.00'), last_modified_by=self.teacher_user)
        response = self.client.get(self.grade_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(Decimal(str(response.data[0]['score'])), Decimal('85.00'))

    def test_teacher_cannot_access_other_teacher_ta_grades(self):
        # 创建另一个老师的TA
        other_teacher_user = CustomUser.objects.create_user(username="other_teacher_api", password="password", role=CustomUser.Role.TEACHER)
        other_teacher_profile = Teacher.objects.create(user=other_teacher_user, teacher_id_num="TOTHER01", name="Other Prof", department=self.department)
        other_ta = TeachingAssignment.objects.create(teacher=other_teacher_profile, course=self.course, semester="2025 Spring")

        url_other_ta_list = reverse('teaching-assignment-grades-list', kwargs={'teaching_assignment_id': other_ta.pk})
        response_list = self.client.get(url_other_ta_list) # 当前登录的是 self.teacher_user
        self.assertEqual(response_list.status_code, status.HTTP_403_FORBIDDEN)

        url_other_ta_detail = reverse(
            'student-grade-for-teaching-assignment-detail',
            kwargs={'teaching_assignment_id': other_ta.pk, 'student_id': self.student_profile.user_id}
        )
        response_detail_put = self.client.put(url_other_ta_detail, {'score': '10'}, format='json')
        self.assertEqual(response_detail_put.status_code, status.HTTP_403_FORBIDDEN)

    # ... 更多API测试用例，如400, 401, 404等 ...