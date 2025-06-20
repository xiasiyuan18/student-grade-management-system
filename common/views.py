from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.core.paginator import Paginator
from django.views import View
from django.contrib import messages
from decimal import Decimal

from courses.models import Course, CourseEnrollment, TeachingAssignment
from grades.models import Grade  # ✅ Grade 在 grades 应用中，不在 courses 中
from departments.models import Department, Major
from users.models import Teacher, Student, CustomUser
from .mixins import (
    RoleRequiredMixin, StudentRequiredMixin, TeacherRequiredMixin,
    SensitiveInfoMixin, OwnDataOnlyMixin
)


def calculate_and_update_student_credits(student):
    """计算并更新学生的学分统计"""
    from decimal import Decimal
    
    # 获取学生所有有效的成绩记录（成绩≥60分才能获得学分）
    passing_grades = Grade.objects.filter(
        student=student,
        score__gte=60,  # 只计算及格的成绩
        teaching_assignment__course__isnull=False
    ).select_related('teaching_assignment__course')
    
    # 计算主修和辅修学分
    major_credits = Decimal("0.0")
    minor_credits = Decimal("0.0")
    
    for grade in passing_grades:
        course = grade.teaching_assignment.course
        credits = course.credits or Decimal("0.0")
        
        # 判断是主修还是辅修课程
        if course.department == student.department:
            # 主修院系的课程算作主修学分
            major_credits += credits
        elif hasattr(student, 'minor_department') and student.minor_department and course.department == student.minor_department:
            # 辅修院系的课程算作辅修学分
            minor_credits += credits
        else:
            # 其他院系的课程默认算作主修学分（选修课等）
            major_credits += credits
    
    # 更新学生的学分统计
    student.credits_earned = major_credits
    if hasattr(student, 'minor_credits_earned'):
        student.minor_credits_earned = minor_credits
    
    student.save(update_fields=["credits_earned", "minor_credits_earned"])
    
    print(f"更新学生 {student.name} 学分: 主修 {major_credits}, 辅修 {minor_credits}")
    
    return {
        'major_credits': major_credits,
        'minor_credits': minor_credits,
        'total_credits': major_credits + minor_credits
    }


class BaseInfoQueryMixin(LoginRequiredMixin):
    """基础信息查询混入类，提供通用的查询权限控制"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class DepartmentListView(BaseInfoQueryMixin, generic.ListView):
    """院系信息查询 - 所有登录用户可访问"""
    model = Department
    template_name = 'common/department_list.html'
    context_object_name = 'departments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Department.objects.all().order_by('dept_name')
        
        # 搜索功能
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(dept_name__icontains=search_query) |
                Q(dept_code__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['page_title'] = '院系信息查询'
        return context


class MajorListView(BaseInfoQueryMixin, generic.ListView):
    """专业信息查询 - 所有登录用户可访问"""
    model = Major
    template_name = 'common/major_list.html'
    context_object_name = 'majors'
    paginate_by = 20

    def get_queryset(self):
        queryset = Major.objects.select_related('department').order_by('department__dept_name', 'major_name')
        
        # 搜索功能 - 添加新字段到搜索范围
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(major_name__icontains=search_query) |
                Q(major_code__icontains=search_query) |
                Q(department__dept_name__icontains=search_query) |
                Q(degree_type__icontains=search_query) |
                Q(duration__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # 按院系筛选
        department_id = self.request.GET.get('department', '')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        # 按学位类型筛选
        degree_type = self.request.GET.get('degree_type', '')
        if degree_type:
            queryset = queryset.filter(degree_type=degree_type)
        
        # 按学制筛选
        duration = self.request.GET.get('duration', '')
        if duration:
            queryset = queryset.filter(duration=duration)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_department'] = self.request.GET.get('department', '')
        context['selected_degree_type'] = self.request.GET.get('degree_type', '')
        context['selected_duration'] = self.request.GET.get('duration', '')
        context['departments'] = Department.objects.all().order_by('dept_name')
        
        # 添加学位类型和学制选项
        context['degree_types'] = Major.DEGREE_TYPE_CHOICES
        context['durations'] = Major.DURATION_CHOICES
        context['page_title'] = '专业信息查询'
        return context


class CourseListView(BaseInfoQueryMixin, generic.ListView):
    """课程信息查询 - 所有登录用户可访问"""
    model = Course
    template_name = 'common/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        queryset = Course.objects.select_related('department').order_by('department__dept_name', 'course_name')
        
        # 搜索功能
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(course_name__icontains=search_query) |
                Q(course_id__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(department__dept_name__icontains=search_query)
            )
        
        # 按院系筛选
        department_id = self.request.GET.get('department', '')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        # 按学分筛选
        min_credits = self.request.GET.get('min_credits', '')
        max_credits = self.request.GET.get('max_credits', '')
        if min_credits:
            queryset = queryset.filter(credits__gte=min_credits)
        if max_credits:
            queryset = queryset.filter(credits__lte=max_credits)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_department'] = self.request.GET.get('department', '')
        context['min_credits'] = self.request.GET.get('min_credits', '')
        context['max_credits'] = self.request.GET.get('max_credits', '')
        context['departments'] = Department.objects.all().order_by('dept_name')
        context['page_title'] = '课程信息查询'
        return context


class TeacherInfoListView(BaseInfoQueryMixin, SensitiveInfoMixin, generic.ListView):
    """教师信息查询 - 根据角色限制访问范围"""
    model = Teacher
    template_name = 'common/teacher_list.html'
    context_object_name = 'teachers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Teacher.objects.select_related('user', 'department').order_by('department__dept_name', 'name')
        
        # 根据用户角色限制查询范围
        user = self.request.user
        if hasattr(user, 'role') and user.role == CustomUser.Role.STUDENT:
            try:
                # 首先检查用户是否有学生档案
                if not hasattr(user, 'student_profile'):
                    print(f"用户 {user.username} 没有学生档案")
                    queryset = queryset.none()
                    return queryset
                
                student_profile = user.student_profile
                if not student_profile:
                    print(f"用户 {user.username} 的学生档案为空")
                    queryset = queryset.none()
                    return queryset
                
                print(f"学生档案: {student_profile.name} ({student_profile.student_id_num})")
                
                # 查询所有选课记录（包括各种状态）
                all_enrollments = CourseEnrollment.objects.filter(student=student_profile)
                print(f"总选课记录数: {all_enrollments.count()}")
                
                for enrollment in all_enrollments:
                    print(f"选课记录: {enrollment.teaching_assignment.course.course_name} - {enrollment.teaching_assignment.teacher.name} - 状态: {enrollment.status}")
                
                # 获取有效选课记录（排除已退课的）
                active_enrollments = all_enrollments.exclude(status='DROPPED')
                print(f"有效选课记录数: {active_enrollments.count()}")
                
                # 获取教师ID列表 - 这里需要根据Teacher模型的实际主键字段来修改
                teacher_ids = list(active_enrollments.values_list('teaching_assignment__teacher_id', flat=True).distinct())
                print(f"相关教师ID列表: {teacher_ids}")
                
                if teacher_ids:
                    # 修复：检查Teacher模型的实际主键字段
                    # 方法1：尝试使用pk（Django的通用主键字段）
                    try:
                        queryset = queryset.filter(pk__in=teacher_ids)
                        print(f"使用pk筛选后的教师数量: {queryset.count()}")
                    except Exception as e1:
                        print(f"使用pk筛选失败: {e1}")
                        # 方法2：尝试使用user_id（如果Teacher模型使用user作为主键）
                        try:
                            queryset = queryset.filter(user_id__in=teacher_ids)
                            print(f"使用user_id筛选后的教师数量: {queryset.count()}")
                        except Exception as e2:
                            print(f"使用user_id筛选失败: {e2}")
                            # 方法3：尝试使用teacher_id_num
                            try:
                                # 需要先获取实际的teacher_id_num值
                                teacher_nums = list(active_enrollments.values_list('teaching_assignment__teacher__teacher_id_num', flat=True).distinct())
                                queryset = queryset.filter(teacher_id_num__in=teacher_nums)
                                print(f"使用teacher_id_num筛选后的教师数量: {queryset.count()}")
                            except Exception as e3:
                                print(f"使用teacher_id_num筛选失败: {e3}")
                                queryset = queryset.none()
                else:
                    print("没有相关教师ID，返回空查询集")
                    queryset = queryset.none()
                
            except Exception as e:
                print(f"查询教师时出错: {e}")
                import traceback
                traceback.print_exc()
                queryset = queryset.none()
        
        # 搜索功能
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(teacher_id_num__icontains=search_query) |
                Q(department__dept_name__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )
        
        # 按院系筛选
        department_id = self.request.GET.get('department', '')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_department'] = self.request.GET.get('department', '')
        context['departments'] = Department.objects.all().order_by('dept_name')
        context['page_title'] = '教师信息查询'
        context['is_student'] = hasattr(self.request.user, 'role') and self.request.user.role == CustomUser.Role.STUDENT
        
        # 为学生用户添加调试信息
        if context['is_student']:
            try:
                student_profile = self.request.user.student_profile
                if student_profile:
                    # 统计选课信息
                    all_enrollments = CourseEnrollment.objects.filter(student=student_profile)
                    active_enrollments = all_enrollments.exclude(status='DROPPED')
                    
                    context['debug_all_enrollment_count'] = all_enrollments.count()
                    context['debug_active_enrollment_count'] = active_enrollments.count()
                    
                    # 获取相关教师数量
                    teacher_ids = active_enrollments.values_list('teaching_assignment__teacher_id', flat=True).distinct()
                    context['debug_teacher_count'] = len(teacher_ids)
                else:
                    context['debug_all_enrollment_count'] = 0
                    context['debug_active_enrollment_count'] = 0
                    context['debug_teacher_count'] = 0
            except:
                context['debug_all_enrollment_count'] = 0
                context['debug_active_enrollment_count'] = 0
                context['debug_teacher_count'] = 0
        
        return context


class StudentInfoView(StudentRequiredMixin, generic.TemplateView):
    """学生个人信息查询 - 仅限学生本人访问"""
    template_name = 'common/student_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            student_profile = self.request.user.student_profile
            context['student'] = student_profile
            context['page_title'] = '个人信息查询'
            
            # 获取选课信息
            if student_profile:
                from courses.models import CourseEnrollment
                enrollments = CourseEnrollment.objects.filter(
                    student=student_profile
                ).select_related(
                    'teaching_assignment__course',
                    'teaching_assignment__teacher'
                ).order_by('-enrollment_date')
                context['enrollments'] = enrollments
                
                # ✅ 实时计算并更新学分
                credit_info = calculate_and_update_student_credits(student_profile)
                context['credit_info'] = credit_info
                
                # ✅ 获取成绩统计信息
                from django.db.models import Avg, Count
                grades = Grade.objects.filter(student=student_profile, score__isnull=False)
                
                if grades.exists():
                    context['total_courses'] = grades.count()
                    context['passed_courses'] = grades.filter(score__gte=60).count()
                    context['average_score'] = grades.aggregate(avg=Avg('score'))['avg']
                    context['grade_distribution'] = {
                        'excellent': grades.filter(score__gte=90).count(),
                        'good': grades.filter(score__gte=80, score__lt=90).count(),
                        'average': grades.filter(score__gte=70, score__lt=80).count(),
                        'pass': grades.filter(score__gte=60, score__lt=70).count(),
                        'fail': grades.filter(score__lt=60).count(),
                    }
                else:
                    context['total_courses'] = 0
                    context['passed_courses'] = 0
                    context['average_score'] = None
                    context['grade_distribution'] = {
                        'excellent': 0, 'good': 0, 'average': 0, 'pass': 0, 'fail': 0
                    }
                
        except Exception as e:
            context['error'] = f"获取学生信息失败: {str(e)}"
        
        return context


class GradeEntryView(TeacherRequiredMixin, View):
    """教师录入成绩"""
    
    def post(self, request, assignment_id):
        assignment = get_object_or_404(TeachingAssignment, pk=assignment_id)
        
        try:
            if assignment.teacher != request.user.teacher_profile:
                messages.error(request, "权限错误")
                return redirect('grades:teacher-courses')
        except AttributeError:
            return redirect('home')
        
        updated_count = 0
        error_count = 0
        updated_students = set()  # ✅ 新增：记录需要更新学分的学生
        
        for key, value in request.POST.items():
            if key.startswith('score_') and value.strip():
                try:
                    student_pk = int(key.replace('score_', ''))
                    score_val = Decimal(value)
                    
                    if not (0 <= score_val <= 100):
                        error_count += 1
                        continue
                    
                    student = get_object_or_404(Student, pk=student_pk)
                    
                    if not CourseEnrollment.objects.filter(student=student, teaching_assignment=assignment, status='ENROLLED').exists():
                        error_count += 1
                        continue
                    
                    grade, created = Grade.objects.update_or_create(
                        student=student,
                        teaching_assignment=assignment,
                        defaults={'score': score_val, 'last_modified_by': request.user}
                    )
                    updated_count += 1
                    updated_students.add(student)  # ✅ 新增：记录学生
                    
                except (ValueError, Student.DoesNotExist):
                    error_count += 1
                    continue
        
        # ✅ 新增：为所有更新了成绩的学生重新计算学分
        for student in updated_students:
            calculate_and_update_student_credits(student)
        
        if updated_count > 0:
            messages.success(request, f"成功录入/更新了 {updated_count} 条成绩记录，并已自动更新相关学生的学分统计。")
        if error_count > 0:
            messages.warning(request, f"有 {error_count} 条记录因数据无效或权限问题而录入失败。")
        
        return redirect('grades:grade-entry', assignment_id=assignment_id)


# common/views.py 中的学生查询视图
def get_queryset(self):
    queryset = Student.objects.select_related(
        'user', 'major', 'department', 'minor_major', 'minor_department'
    ).order_by('student_id_num')
    
    search_query = self.request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(student_id_num__icontains=search_query) |
            Q(major__major_name__icontains=search_query) |
            Q(department__dept_name__icontains=search_query) |
            Q(minor_major__major_name__icontains=search_query) |
            Q(minor_department__dept_name__icontains=search_query)
        )
    
    return queryset

import pandas as pd
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView
from datetime import datetime

from departments.models import Department, Major
from users.models import CustomUser, Student
# Remove the problematic import - forms module doesn't exist
# from .forms import StudentImportForm
# ✅ 修改：使用现有的 AdminRequiredMixin 替代不存在的函数
from common.mixins import AdminRequiredMixin
from django import forms

# Define the form class directly here since forms module doesn't exist
class StudentImportForm(forms.Form):
    file = forms.FileField(
        label="选择Excel文件",
        help_text="请上传包含学生信息的Excel文件(.xlsx格式)"
    )


class StudentImportView(AdminRequiredMixin, FormView):  # ✅ 使用 AdminRequiredMixin
    template_name = "utils/student_import.html"
    form_class = StudentImportForm
    success_url = reverse_lazy("users:student-list")

    # ✅ 删除：不再需要 dispatch 方法，AdminRequiredMixin 会自动处理权限
    # def dispatch(self, request, *args, **kwargs):
    #     if not is_admin_or_teacher_or_manager(request.user):
    #         messages.error(request, "您没有权限访问此页面。")
    #         return redirect("core:home")
    #     return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        file = form.cleaned_data["file"]

        try:
            df = pd.read_excel(file).astype(str).replace('nan', '')
        except Exception as e:
            messages.error(self.request, f"文件读取失败，请确保是有效的 .xlsx 文件。错误: {e}")
            return super().form_invalid(form)

        required_columns = {
            "username", "password", "name", "student_id_num", "department_name", "major_name"
        }
        
        if not required_columns.issubset(df.columns):
            missing_cols = required_columns - set(df.columns)
            messages.error(self.request, f"文件缺少必需的列: {', '.join(missing_cols)}")
            return super().form_invalid(form)

        errors = []
        for index, row in df.iterrows():
            row_num = index + 2
            try:
                # --- 获取数据 ---
                username = row["username"].strip()
                password = row["password"].strip()
                name = row["name"].strip()
                student_id_num = row["student_id_num"].strip()
                department_name = row["department_name"].strip()
                major_name = row["major_name"].strip()
                
                # 新增：获取辅修院系和专业
                minor_department_name = row.get("minor_department_name", "").strip()
                minor_major_name = row.get("minor_major_name", "").strip()

                # --- 数据校验 ---
                if not all([username, password, name, student_id_num, department_name, major_name]):
                    errors.append(f"第 {row_num} 行：必填字段（username, password, name, student_id_num, department_name, major_name）不能为空。")
                    continue
                
                if CustomUser.objects.filter(username=username).exists() or Student.objects.filter(student_id_num=student_id_num).exists():
                    errors.append(f"第 {row_num} 行：用户名 '{username}' 或学号 '{student_id_num}' 已存在。")
                    continue

                # --- 核心逻辑：根据院系和专业名查找对象 ---
                try:
                    department = Department.objects.get(dept_name=department_name)  # ✅ 修正字段名
                    major = Major.objects.get(major_name=major_name, department=department)  # ✅ 修正字段名
                except Department.DoesNotExist:
                    errors.append(f"第 {row_num} 行：主修院系 '{department_name}' 不存在。")
                    continue
                except Major.DoesNotExist:
                    errors.append(f"第 {row_num} 行：在 '{department_name}' 院系下找不到主修专业 '{major_name}'。")
                    continue

                minor_major = None
                minor_department = None
                if minor_department_name and minor_major_name:
                    try:
                        minor_department = Department.objects.get(dept_name=minor_department_name)  # ✅ 修正字段名
                        minor_major = Major.objects.get(major_name=minor_major_name, department=minor_department)  # ✅ 修正字段名
                    except Department.DoesNotExist:
                        errors.append(f"第 {row_num} 行：辅修院系 '{minor_department_name}' 不存在。")
                        continue
                    except Major.DoesNotExist:
                        errors.append(f"第 {row_num} 行：在 '{minor_department_name}' 院系下找不到辅修专业 '{minor_major_name}'。")
                        continue
                
                # --- 创建对象 ---
                user = CustomUser.objects.create_user(
                    username=username, 
                    password=password, 
                    first_name=name,  # ✅ 使用 first_name 而不是 full_name
                    role=CustomUser.Role.STUDENT  # ✅ 使用正确的角色枚举
                )
                Student.objects.create(
                    user=user, 
                    student_id_num=student_id_num,  # ✅ 修正字段名
                    name=name,
                    major=major, 
                    department=department,
                    minor_major=minor_major,
                    minor_department=minor_department,
                    gender=row.get("gender", "男").strip(),
                    birth_date=pd.to_datetime(row.get('birth_date'), errors='coerce').date() if row.get('birth_date') else None,
                    phone=row.get("phone", "").strip(),
                )

            except Exception as e:
                errors.append(f"处理第 {row_num} 行时发生未知错误: {e}")

        if errors:
            transaction.set_rollback(True)
            for error in errors:
                messages.error(self.request, error)
            return super().form_invalid(form)

        messages.success(self.request, f"学生批量导入成功！共导入 {len(df)} 条记录。")
        return super().form_valid(form)