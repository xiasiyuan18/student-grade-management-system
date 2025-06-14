from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.core.paginator import Paginator

from departments.models import Department, Major
from courses.models import Course, CourseEnrollment
from users.models import Teacher, Student, CustomUser
from .mixins import (
    RoleRequiredMixin, StudentRequiredMixin, 
    SensitiveInfoMixin, OwnDataOnlyMixin
)


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
        
        # 搜索功能
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(major_name__icontains=search_query) |
                Q(major_code__icontains=search_query) |
                Q(department__dept_name__icontains=search_query) |
                Q(degree_type__icontains=search_query)
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
                
        except Exception as e:
            context['error'] = f"获取学生信息失败: {str(e)}"
        
        return context