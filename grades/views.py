# student_grade_management_system/grades/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db import transaction # 用于事务操作
from django.http import HttpResponseRedirect # 用于重定向

from .models import Grade
from .forms import GradeEntryForm, SelectTeachingAssignmentForm
from courses.models import TeachingAssignment
from users.models import Student, CustomUser # 导入 Student 和 CustomUser 模型

# 辅助函数：检查用户角色
def is_teacher_or_admin(user):
    # 确保 user.CustomUser.Role 存在，因为它是枚举
    return user.is_superuser or (hasattr(user, 'role') and (user.role == CustomUser.Role.ADMIN or user.role == CustomUser.Role.TEACHER))

# --- 成绩录入/修改视图 (教师视角) ---

class GradeEntryView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'grades/grade_entry_form.html'

    def test_func(self):
        # 只有教师和管理员有权限进行成绩录入
        return is_teacher_or_admin(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "您没有权限访问成绩录入页面。")
        return super().handle_no_permission()

    def get(self, request, *args, **kwargs):
        select_form = SelectTeachingAssignmentForm(user=request.user)
        teaching_assignment_id = request.GET.get('assignment_id')
        students_grades = []
        assignment = None

        if teaching_assignment_id:
            try:
                # 确保是当前教师的授课，并且教学安排存在
                assignment = TeachingAssignment.objects.get(pk=teaching_assignment_id)
                if self.request.user.is_authenticated and self.request.user.role == CustomUser.Role.TEACHER:
                    # 仅限教师访问自己的授课安排
                    if assignment.teacher != self.request.user.teacher_profile:
                        raise TeachingAssignment.DoesNotExist # 伪造一个 DoesNotExist 异常
                elif not self.request.user.is_superuser and self.request.user.role != CustomUser.Role.ADMIN:
                    # 非管理员和非超级用户无权访问
                    raise TeachingAssignment.DoesNotExist

                # 获取与该授课安排相关的学生。这部分逻辑需要根据你的实际数据模型和选课逻辑调整。
                # 假设：我们可以通过 TeachingAssignment 获取其关联的课程，然后找到所有选修了该课程的学生。
                # 或者：如果 Grade 表已经有数据，直接从 Grade 表中获取学生。
                # 简化的做法是：获取所有学生，然后筛选那些可能关联的。
                # 更理想的场景：如果你的项目有 Enrollment（选课）模型，应该通过它来获取学生
                # For now, let's assume all students can be scored for any course they are enrolled in.
                # Since there's no Enrollment model provided, we'll try to find students who might have a grade or are generally in the system.
                # A more robust solution might require fetching students enrolled in `assignment.course`.

                # For simplicity, we'll fetch all students and attempt to retrieve their grades.
                # In a real system, you'd filter this to students enrolled in `assignment.course`.
                all_students = Student.objects.all().order_by('user__username')

                # 预填充学生和成绩，如果学生有该门课的成绩
                for student in all_students:
                    try:
                        grade_obj = Grade.objects.get(student=student, teaching_assignment=assignment)
                        initial_score = grade_obj.score
                    except Grade.DoesNotExist:
                        grade_obj = None
                        initial_score = None

                    # 为每个学生创建 GradeEntryForm
                    form = GradeEntryForm(
                        instance=grade_obj, # 如果存在成绩对象，则用于更新
                        initial={'student': student.pk, 'teaching_assignment': assignment.pk, 'score': initial_score}
                    )
                    students_grades.append({'student': student, 'form': form, 'grade_obj_id': grade_obj.pk if grade_obj else None})

            except TeachingAssignment.DoesNotExist:
                messages.error(request, "选择的授课安排无效或您无权访问。")
                teaching_assignment_id = None # 重置，避免显示错误信息
            except Exception as e:
                messages.error(request, f"加载授课安排时发生错误: {e}")
                teaching_assignment_id = None


        context = {
            'select_form': select_form,
            'teaching_assignment_id': teaching_assignment_id,
            'assignment': assignment,
            'students_grades': students_grades, # 包含每个学生的表单
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # 处理选择授课安排的 POST 请求 (如果用户只是点击了“选择”按钮)
        if 'select_assignment' in request.POST:
            select_form = SelectTeachingAssignmentForm(request.POST, user=request.user)
            if select_form.is_valid():
                selected_assignment_id = select_form.cleaned_data['teaching_assignment'].pk
                return redirect(reverse_lazy('grades:grade_entry') + f'?assignment_id={selected_assignment_id}')
            else:
                messages.error(request, "选择授课安排失败，请重试。")
                return redirect(reverse_lazy('grades:grade_entry'))

        # 处理成绩提交的 POST 请求
        teaching_assignment_id = request.POST.get('assignment_id')

        if not teaching_assignment_id:
            messages.error(request, "请先选择授课安排。")
            return redirect(reverse_lazy('grades:grade_entry'))

        try:
            assignment = TeachingAssignment.objects.get(pk=teaching_assignment_id)
            if self.request.user.is_authenticated and self.request.user.role == CustomUser.Role.TEACHER:
                if assignment.teacher != self.request.user.teacher_profile:
                    messages.error(request, "您无权修改此授课安排的成绩。")
                    return redirect(reverse_lazy('grades:grade_entry'))
            elif not self.request.user.is_superuser and self.request.user.role != CustomUser.Role.ADMIN:
                messages.error(request, "您无权修改此授课安排的成绩。")
                return redirect(reverse_lazy('grades:grade_entry'))

        except TeachingAssignment.DoesNotExist:
            messages.error(request, "选择的授课安排无效或您无权访问。")
            return redirect(reverse_lazy('grades:grade_entry'))

        # 批量处理成绩
        success_count = 0
        error_count = 0

        # 获取所有学生的ID，用于遍历POST数据
        # 实际项目中，这里应该获取该课程或班级下所有应得分的学生
        all_students_in_context = Student.objects.all() # 简化，实际应根据 assignment 筛选
        student_pks = [s.pk for s in all_students_in_context]


        with transaction.atomic(): # 确保所有更新是原子性的
            for student_pk in student_pks:
                form_prefix = f"student_{student_pk}_"
                score_key = f"{form_prefix}score"
                grade_obj_id_key = f"{form_prefix}grade_obj_id"

                score_value = request.POST.get(score_key)
                grade_obj_id = request.POST.get(grade_obj_id_key)

                student_obj = get_object_or_404(Student, pk=student_pk) # 获取学生实例

                # 只有当分数被提交 (非空且非空字符串) 或明确请求删除时才处理
                if score_value is not None and score_value != '':
                    try:
                        # 尝试获取现有成绩对象或创建新对象
                        if grade_obj_id:
                            grade_obj = Grade.objects.get(pk=grade_obj_id, student=student_obj, teaching_assignment=assignment)
                        else:
                            # 检查是否已有成绩存在，避免重复创建
                            try:
                                grade_obj = Grade.objects.get(student=student_obj, teaching_assignment=assignment)
                            except Grade.DoesNotExist:
                                grade_obj = Grade(student=student_obj, teaching_assignment=assignment)

                        # 创建表单实例并绑定数据
                        # 注意：这里我们只更新分数，student和teaching_assignment是固定值
                        form = GradeEntryForm(
                            {'score': score_value, 'student': student_obj.pk, 'teaching_assignment': assignment.pk},
                            instance=grade_obj
                        )

                        if form.is_valid():
                            grade_instance = form.save(commit=False)
                            grade_instance.last_modified_by = request.user
                            grade_instance.save()
                            success_count += 1
                        else:
                            # 记录每个学生的错误，但继续处理其他学生
                            error_message = ""
                            for field_name, errors in form.errors.items():
                                error_message += f"{field_name}: {', '.join(errors)}; "
                            messages.error(request, f"学生 {student_obj.user.username} 成绩录入失败: {error_message}")
                            error_count += 1
                    except Exception as e:
                        messages.error(request, f"处理学生 {student_obj.user.username} 成绩时发生错误: {e}")
                        error_count += 1
                elif request.POST.get(f"delete_student_{student_pk}") == 'on': # 如果前端有删除复选框，并且被选中
                    try:
                        grade_obj = Grade.objects.get(student=student_obj, teaching_assignment=assignment)
                        grade_obj.delete()
                        messages.info(request, f"学生 {student_obj.user.username} 的成绩已删除。")
                    except Grade.DoesNotExist:
                        pass # 已经不存在，无需处理
                    except Exception as e:
                        messages.error(request, f"删除学生 {student_obj.user.username} 成绩时发生错误: {e}")

        if success_count > 0:
            messages.success(request, f"成功更新/录入 {success_count} 条成绩。")
        if error_count > 0:
            messages.warning(request, f"有 {error_count} 条成绩录入失败。")
        elif success_count == 0 and error_count == 0:
            messages.info(request, "没有检测到需要更新的成绩。")

        # 成功处理后，重定向回当前授课安排的录入页面
        return redirect(reverse_lazy('grades:grade_entry') + f'?assignment_id={assignment.pk}')