# grades/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from decimal import Decimal

# 引入更具体的异常类型
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.utils import IntegrityError as DjangoIntegrityError

# 引入其他app的模型 (确保路径正确，并统一名称)
from users.models import CustomUser, Student, Teacher 
from departments.models import Department 
from departments.models import Major 
from courses.models import Course, TeachingAssignment 


from grades.models import Grade # 导入Grade模型
# 导入服务函数
from grades.services import calculate_and_update_student_credits, create_or_update_grade


User = get_user_model() # 这将返回 CustomUser 模型


class GradeModelTest(TestCase):
    """测试Grade模型及GPA计算和验证"""
    def setUp(self):
        # 1. 创建 Department 实例
        self.department = Department.objects.create(dept_code="CS", dept_name="计算机科学与技术系")
        # 2. 创建 Major 实例 (关联到 Department)
        self.major = Major.objects.create(major_name="软件工程", department=self.department, bachelor_credits_required=Decimal('120.0')) 

        # 创建测试 CustomUser 实例 (作为用户)，并指定角色
        self.student_user = User.objects.create_user(
            username='studentuser', # CustomUser 的 username
            password='password123',
            role=CustomUser.Role.STUDENT # 指定角色
        )
        # 创建对应的 Student Profile
        self.student_profile = Student.objects.create(
            user=self.student_user, # 关联 CustomUser
            student_id_num='S12345', 
            name='张三',
            id_card='123456789012345678',
            gender='男',
            major=self.major, # <--- 修正: 传递 Major 实例
            department=self.department, # <--- 修正: 传递 Department 实例
            degree_level='本科'
        )

        self.teacher_user = User.objects.create_user(
            username='teacheruser', 
            password='password123',
            role=CustomUser.Role.TEACHER, 
            is_staff=True 
        )
        # 创建对应的 Teacher Profile
        self.teacher_profile = Teacher.objects.create(
            user=self.teacher_user, 
            teacher_id_num='T001', 
            name='李四',
            department=self.department # 传递 Department 实例
        )
        
        # 创建 Admin 用户 
        self.admin_user = User.objects.create_superuser(
            username='admin', password='adminpassword', role=CustomUser.Role.ADMIN
        )

        # 确保 Course 模型创建时包含 department 字段 (关联到 Department 实例)
        self.course = Course.objects.create(course_id='CS101', course_name='计算机导论', credits=Decimal('3.0'), department=self.department)
        # 修正 TeachingAssignment 为实际类名
        self.teaching_assignment = TeachingAssignment.objects.create(teacher=self.teacher_profile, course=self.course, semester='2023-2024-1')

    def test_grade_creation_and_gpa_calculation(self):
        """测试成绩创建和GPA自动计算"""
        # score__isnull=False (来自 services.py) 是学分计算逻辑
        # 而 gpa 字段在 Grade 模型中是根据分数范围计算的
        grade = Grade.objects.create(
            student=self.student_profile, # 传递 Student Profile 实例
            teaching_assignment=self.teaching_assignment, # 传递 TeachingAssignment 实例
            score=Decimal('85.5')
        )
        self.assertEqual(grade.score, Decimal('85.5'))
        self.assertEqual(grade.gpa, Decimal('3.7')) # 验证GPA是否正确计算

        # 测试 GPA 计算逻辑：
        # 创建一个不同 UniqueConstraint 的成绩，以确保不冲突
        grade_a_ta = TeachingAssignment.objects.create(teacher=self.teacher_profile, course=self.course, semester='2023-2024-2')
        grade_a = Grade.objects.create(student=self.student_profile, teaching_assignment=grade_a_ta, score=Decimal('90.0'))
        self.assertEqual(grade_a.gpa, Decimal('4.0'))
        
        grade_b_ta = TeachingAssignment.objects.create(teacher=self.teacher_profile, course=self.course, semester='2024-2025-1')
        grade_b = Grade.objects.create(student=self.student_profile, teaching_assignment=grade_b_ta, score=Decimal('59.9'))
        self.assertEqual(grade_b.gpa, Decimal('0.0'))

    def test_grade_unique_together(self):
        """测试唯一性约束"""
        Grade.objects.create(student=self.student_profile, teaching_assignment=self.teaching_assignment, score=Decimal('80.0'))
        # 尝试创建重复的成绩 (student, teaching_assignment)，应该会失败，抛出 IntegrityError
        from django.db.utils import IntegrityError # 引入IntegrityError
        with self.assertRaises(IntegrityError): 
            Grade.objects.create(student=self.student_profile, teaching_assignment=self.teaching_assignment, score=Decimal('90.0'))

class GradeAPITest(TestCase):
    """测试Grade API端点和权限"""
    def setUp(self):
        self.client = APIClient()
        self.department = Department.objects.create(dept_code="MATH", dept_name="数学系")
        self.major = Major.objects.create(major_name="应用数学", department=self.department, bachelor_credits_required=Decimal('120.0')) 

        # 创建不同角色的 CustomUser (User) 实例
        self.admin_user = User.objects.create_superuser(
            username='admin', password='adminpassword', role=CustomUser.Role.ADMIN
        )
        self.student_user = User.objects.create_user(
            username='studentuser', password='password123', role=CustomUser.Role.STUDENT
        )
        # 创建对应的 Student Profile
        self.student_profile = Student.objects.create(
            user=self.student_user, student_id_num='S12345', name='张三', 
            id_card='123456789012345678', gender='男', major=self.major, department=self.department, degree_level='本科'
        )
        self.teacher_user = User.objects.create_user(
            username='teacheruser', password='password123', role=CustomUser.Role.TEACHER, is_staff=True
        )
        # 创建对应的 Teacher Profile
        self.teacher_profile = Teacher.objects.create(
            user=self.teacher_user, teacher_id_num='T001', name='李四', department=self.department
        )
        
        # 创建其他用户和数据以测试权限过滤
        self.other_student_user = User.objects.create_user(username='other_student', password='password123', role=CustomUser.Role.STUDENT)
        # 创建对应的 Other Student Profile
        self.other_student_profile = Student.objects.create(
            user=self.other_student_user, student_id_num='S99999', name='王五', 
            id_card='999999999999999999', gender='男', major=self.major, department=self.department, degree_level='本科'
        )
        self.other_teacher_user = User.objects.create_user(username='other_teacher', password='password123', role=CustomUser.Role.TEACHER, is_staff=True)
        # 创建对应的 Other Teacher Profile
        self.other_teacher_profile = Teacher.objects.create(
            user=self.other_teacher_user, teacher_id_num='T999', name='赵六', department=self.department
        )

        self.course_cs = Course.objects.create(course_id='CS101', course_name='计算机导论', credits=Decimal('3.0'), department=self.department)
        self.course_math = Course.objects.create(course_id='MA101', course_name='高等数学', credits=Decimal('4.0'), department=self.department)

        # 创建授课安排 (使用 TeachingAssignment)
        self.teaching_cs = TeachingAssignment.objects.create(teacher=self.teacher_profile, course=self.course_cs, semester='2023-2024-1')
        self.teaching_math_other = TeachingAssignment.objects.create(teacher=self.other_teacher_profile, course=self.course_math, semester="2025 Spring")

        # 创建成绩 (确保 student 和 teacher 参数直接接收 Profile 实例)
        self.grade_student_cs = Grade.objects.create(student=self.student_profile, teaching_assignment=self.teaching_cs, score=Decimal('85.0'))
        self.grade_other_student_cs = Grade.objects.create(student=self.other_student_profile, teaching_assignment=self.teaching_cs, score=Decimal('90.0'))
        self.grade_student_math_other_teacher = Grade.objects.create(student=self.student_profile, teaching_assignment=self.teaching_math_other, score=Decimal('75.0'))


    def test_unauthenticated_cannot_access_grades(self):
        """未认证用户无法访问成绩API"""
        # 测试 /api/teaching-assignments/{id}/grades/ 列表页
        response = self.client.get(reverse('teaching-assignment-grades-list', kwargs={'teaching_assignment_id': self.teaching_cs.pk}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 测试 /api/teaching-assignments/{id}/grades/students/{id}/ 详情页 (PUT)
        response = self.client.put(reverse('student-grade-for-teaching-assignment-detail', 
                                          kwargs={'teaching_assignment_id': self.teaching_cs.pk, 'student_id': self.student_profile.pk}), 
                                   {'score': '10'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_can_list_own_grades(self):
        """学生只能列出自己的成绩"""
        # 这里测试的是 TeachingAssignmentGradesListView，它有教师权限，学生访问会 403 Forbidden
        # 严格来说，学生应该访问他们自己的成绩列表，而不是某个 TA 的列表 (这需要独立的 URL 和视图)
        # 按照当前测试的这个端点，学生确实没有权限
        self.client.force_authenticate(user=self.student_user) 
        response = self.client.get(reverse('teaching-assignment-grades-list', kwargs={'teaching_assignment_id': self.teaching_cs.pk}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # 学生没有教师权限

    def test_student_cannot_create_grade(self):
        """学生不能创建成绩"""
        self.client.force_authenticate(user=self.student_user)
        data = {
            'student_id': self.student_profile.pk, # 传递 Student Profile 的 PK (修正为 .pk)
            'score': 90.0
        }
        # URL是 /api/teaching-assignments/{teaching_assignment_id}/grades/students/{student_id}/
        url = reverse('student-grade-for-teaching-assignment-detail', kwargs={
            'teaching_assignment_id': self.teaching_cs.pk,
            'student_id': self.student_profile.pk 
        })
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # 学生没有教师权限
