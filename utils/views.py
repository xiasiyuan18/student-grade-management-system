# utils/views.py (已修正)

import pandas as pd
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy

from .forms import FileUploadForm
from common.mixins import AdminRequiredMixin
from users.models import Student
from departments.models import Department, Major

User = get_user_model()

class StudentBulkImportView(AdminRequiredMixin, generic.FormView):
    """
    管理员批量导入学生的视图 (更健壮的版本)。
    """
    template_name = 'utils/student_import.html'
    form_class = FileUploadForm
    success_url = reverse_lazy('users:student-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '批量导入学生'
        return context

    def form_valid(self, form):
        file = form.cleaned_data['file']
        required_columns = ['username', 'password', 'name', 'student_id_num', 'department_name', 'major_name']
        
        try:
            if file.name.endswith('.xlsx'):
                df = pd.read_excel(file, dtype=str)
            elif file.name.endswith('.csv'):
                df = pd.read_csv(file, dtype=str)
            else:
                messages.error(self.request, "文件格式不支持，请上传 .xlsx 或 .csv 文件。")
                return redirect('utils:student-bulk-import')

            if not all(col in df.columns for col in required_columns):
                missing_cols = ", ".join([col for col in required_columns if col not in df.columns])
                messages.error(self.request, f"文件格式错误：您的文件缺少必要的列: {missing_cols}。请下载并使用模板。")
                return redirect('utils:student-bulk-import')

            df.fillna('', inplace=True)
            
            users_to_create = []
            students_to_link = [] # 用于存储学生数据和其关联的用户名
            errors = []
            
            # --- 核心修正逻辑开始 ---
            with transaction.atomic():
                # 阶段一：数据校验和准备
                for index, row in df.iterrows():
                    row_num = index + 2
                    
                    # 校验必填字段
                    if any(pd.isna(row.get(field)) or str(row.get(field)).strip() == '' for field in required_columns):
                        errors.append(f"第 {row_num} 行：缺少必填字段（用户名、密码、姓名、学号、院系、专业）。")
                        continue
                    
                    # 校验用户名和学号是否已存在
                    if User.objects.filter(username=row['username']).exists() or Student.objects.filter(student_id_num=row['student_id_num']).exists():
                        errors.append(f"第 {row_num} 行：用户名 '{row['username']}' 或学号 '{row['student_id_num']}' 已存在。")
                        continue
                    
                    # 校验院系和专业是否存在
                    try:
                        department = Department.objects.get(dept_name=row['department_name'])
                        major = Major.objects.get(major_name=row['major_name'], department=department)
                    except Department.DoesNotExist:
                        errors.append(f"第 {row_num} 行：院系 '{row['department_name']}' 不存在。")
                        continue
                    except Major.DoesNotExist:
                        errors.append(f"第 {row_num} 行：在 '{row['department_name']}' 院系下找不到专业 '{row['major_name']}'。")
                        continue

                    # 准备 User 对象（不保存）
                    user = User(username=row['username'], role=User.Role.STUDENT)
                    user.set_password(row['password'])
                    users_to_create.append(user)

                    # 准备 Student 数据，并暂存用户名用于后续关联
                    student_data = {
                        'username': row['username'], # 关键：暂存用户名
                        'data': {
                            'name': row['name'], 'student_id_num': row['student_id_num'],
                            'id_card': row.get('id_card', ''), 'gender': row.get('gender', '男'),
                            'department': department, 'major': major,
                            'birth_date': pd.to_datetime(row.get('birth_date'), errors='coerce').date() if row.get('birth_date') else None,
                            'phone': row.get('phone', ''),
                        }
                    }
                    students_to_link.append(student_data)

                # 如果在校验阶段发现任何错误，则中断并回滚事务
                if errors:
                    raise IntegrityError("数据校验失败")

                # 阶段二：批量创建用户（不依赖返回值）
                User.objects.bulk_create(users_to_create)

                # 阶段三：根据用户名，重新从数据库获取刚创建的用户（确保获得ID）
                usernames = [user.username for user in users_to_create]
                user_map = {user.username: user for user in User.objects.filter(username__in=usernames)}

                # 阶段四：准备学生对象列表，关联上已保存的用户
                students_to_create = []
                for student_info in students_to_link:
                    username = student_info['username']
                    user_obj = user_map.get(username)
                    if user_obj: # 确保用户已成功创建并找到
                        student_instance = Student(user=user_obj, **student_info['data'])
                        students_to_create.append(student_instance)

                # 阶段五：批量创建学生
                if students_to_create:
                    Student.objects.bulk_create(students_to_create)

                if not errors:
                    messages.success(self.request, f"成功导入 {len(students_to_create)} 名学生！")

        except IntegrityError:
            for error in errors:
                messages.error(self.request, error)
            messages.error(self.request, "导入失败，事务已回滚。请修正文件中的错误后重试。")
            return redirect('utils:student-bulk-import')
        
        except Exception as e:
            messages.error(self.request, f"处理文件时发生未知错误: {e}")
            return redirect('utils:student-bulk-import')

        return super().form_valid(form)
