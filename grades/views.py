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
        # 初始加载或处理选择授课安排的 GET 请求
        teaching_assignment_id = request.GET.get('assignment_id')
        students_grades = []
        assignment = None
        
        # 始终初始化 select_form，以便在页面加载时（无论是否有 assignment_id）都能显示
        select_form = SelectTeachingAssignmentForm(user=request.user)

        if teaching_assignment_id:
            try:
                # 获取授课安排实例
                assignment = TeachingAssignment.objects.get(pk=teaching_assignment_id)
                
                # 权限检查：确保当前教师只能访问自己的授课安排，或管理员访问所有
                user_is_teacher = self.request.user.is_authenticated and hasattr(self.request.user, 'role') and self.request.user.role == CustomUser.Role.TEACHER
                user_is_admin = self.request.user.is_superuser or (self.request.user.is_authenticated and hasattr(self.request.user, 'role') and self.request.user.role == CustomUser.Role.ADMIN)

                if user_is_teacher and assignment.teacher != self.request.user.teacher_profile:
                    messages.error(request, "您无权访问此授课安排。")
                    return redirect(reverse_lazy('grades:grade_entry')) # 重定向回不带参数的页面
                elif not user_is_admin and not user_is_teacher:
                    messages.error(request, "您无权访问此授课安排。")
                    return redirect(reverse_lazy('grades:grade_entry')) # 重定向回不带参数的页面

                # --- 核心：获取与该授课安排相关的学生，并准备成绩表单 ---
                # 在实际应用中，这里应该精确获取选修了该课程的学生。
                # 目前为了简化，我们获取所有学生。如果学生未显示，请确保有 Student 实例存在。
                all_students_for_assignment = Student.objects.all().order_by('user__username') 
                
                # 调试打印：确认学生数量
                print(f"DEBUG(GET): Found {all_students_for_assignment.count()} students from DB.") # <--- 确认这里有这行

                for student in all_students_for_assignment:
                    print(f"DEBUG(GET): Processing student {student.pk} ({student.name or student.user.username})") # <--- 确认这里有这行
                    
                    grade_obj = None
                    initial_score = None
                    try:
                        grade_obj = Grade.objects.get(student=student, teaching_assignment=assignment)
                        initial_score = grade_obj.score
                    except Grade.DoesNotExist:
                        pass # 没有找到现有成绩，initial_score 保持 None
                    
                    # 为每个学生准备一个 GradeEntryForm
                    form = GradeEntryForm(
                        instance=grade_obj, # 如果存在成绩对象，则用于更新
                        initial={
                            'student': student.pk,
                            'teaching_assignment': assignment.pk,
                            'score': initial_score
                        }
                    )
                    students_grades.append({
                        'student': student,
                        'form': form,
                        'grade_obj_id': grade_obj.pk if grade_obj else None
                    })
                
                # 调试打印：确认 students_grades 列表是否被填充
                print(f"DEBUG(GET): students_grades list prepared with {len(students_grades)} entries.") # <--- 确认这里有这行

                # 如果有 assignment_id，则 select_form 应该预选该授课安排
                select_form = SelectTeachingAssignmentForm(initial={'teaching_assignment': assignment.pk}, user=request.user)

            except TeachingAssignment.DoesNotExist:
                messages.error(request, "选择的授课安排无效或您无权访问。")
                teaching_assignment_id = None 
                assignment = None # 清空 assignment
                select_form = SelectTeachingAssignmentForm(user=request.user) # 重置 select_form
            except Exception as e:
                messages.error(request, f"加载授课安排或学生成绩时发生错误: {e}")
                teaching_assignment_id = None
                assignment = None # 清空 assignment
                select_form = SelectTeachingAssignmentForm(user=request.user) # 重置 select_form

        context = {
            'select_form': select_form,
            'teaching_assignment_id': teaching_assignment_id,
            'assignment': assignment,
            'students_grades': students_grades, # 包含每个学生的表单
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # 这个 post 方法只处理成绩提交。
        # 选择授课安排的逻辑现在完全由 GET 方法处理。

        teaching_assignment_id = request.POST.get('assignment_id')

        if not teaching_assignment_id:
            messages.error(request, "请先选择授课安排。")
            return redirect(reverse_lazy('grades:grade_entry'))

        try:
            assignment = TeachingAssignment.objects.get(pk=teaching_assignment_id)
            # 权限检查
            user_is_teacher = self.request.user.is_authenticated and hasattr(self.request.user, 'role') and self.request.user.role == CustomUser.Role.TEACHER
            user_is_admin = self.request.user.is_superuser or (self.request.user.is_authenticated and hasattr(self.request.user, 'role') and self.request.user.role == CustomUser.Role.ADMIN)

            if user_is_teacher and assignment.teacher != self.request.user.teacher_profile:
                messages.error(request, "您无权修改此授课安排的成绩。")
                return redirect(reverse_lazy('grades:grade_entry'))
            elif not user_is_admin and not user_is_teacher:
                messages.error(request, "您无权修改此授课安排的成绩。")
                return redirect(reverse_lazy('grades:grade_entry'))

        except TeachingAssignment.DoesNotExist:
            messages.error(request, "选择的授课安排无效或您无权访问。")
            return redirect(reverse_lazy('grades:grade_entry'))
        except Exception as e:
            messages.error(request, f"处理授课安排时发生错误: {e}")
            return redirect(reverse_lazy('grades:grade_entry'))

        # 获取所有学生的ID，用于遍历POST数据
        # 实际项目中，这里应该获取该课程或班级下所有应得分的学生
        all_students_for_assignment = Student.objects.all() # 简化，实际应根据 assignment 筛选
        student_pks = [s.pk for s in all_students_for_assignment]


        success_count = 0
        error_count = 0
        
        with transaction.atomic():
            for student_pk in student_pks:
                form_prefix = f"student_{student_pk}_"
                score_key = f"{form_prefix}score"
                grade_obj_id_key = f"{form_prefix}grade_obj_id"

                score_value = request.POST.get(score_key)
                grade_obj_id = request.POST.get(grade_obj_id_key)

                student_obj = get_object_or_404(Student, pk=student_pk) 

                if score_value is not None and score_value != '':
                    try:
                        if grade_obj_id:
                            grade_obj = Grade.objects.get(pk=grade_obj_id, student=student_obj, teaching_assignment=assignment)
                        else:
                            try:
                                grade_obj = Grade.objects.get(student=student_obj, teaching_assignment=assignment)
                            except Grade.DoesNotExist:
                                grade_obj = Grade(student=student_obj, teaching_assignment=assignment)
                        
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
                            error_message = ""
                            for field_name, errors in form.errors.items():
                                error_message += f"{field_name}: {', '.join(errors)}; "
                            messages.error(request, f"学生 {student_obj.user.username} 成绩录入失败: {error_message}")
                            error_count += 1
                    except Exception as e:
                        messages.error(request, f"处理学生 {student_obj.user.username} 成绩时发生错误: {e}")
                        error_count += 1
                elif request.POST.get(f"delete_student_{student_pk}") == 'on':
                    try:
                        grade_obj = Grade.objects.get(student=student_obj, teaching_assignment=assignment)
                        grade_obj.delete()
                        messages.info(request, f"学生 {student_obj.user.username} 的成绩已删除。")
                    except Grade.DoesNotExist:
                        pass
                    except Exception as e:
                        messages.error(request, f"删除学生 {student_obj.user.username} 成绩时发生错误: {e}")

        if success_count > 0:
            messages.success(request, f"成功更新/录入 {success_count} 条成绩。")
        if error_count > 0:
            messages.warning(request, f"有 {error_count} 条成绩录入失败。")
        elif success_count == 0 and error_count == 0:
            messages.info(request, "没有检测到需要更新的成绩。")

        # 成功处理 POST 请求后，始终重定向到 GET 请求，以遵循 PRG 模式
        return redirect(reverse_lazy('grades:grade_entry') + f'?assignment_id={assignment.pk}')