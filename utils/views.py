# utils/views.py

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
    管理员批量导入学生的视图。
    """
    template_name = 'utils/student_import.html'
    form_class = FileUploadForm
    success_url = reverse_lazy('users:student-list') # 使用 reverse_lazy

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '批量导入学生'
        return context

    def form_valid(self, form):
        file = form.cleaned_data['file']
        
        try:
            # 根据文件类型读取数据
            if file.name.endswith('.xlsx'):
                # 使用 str 类型读取所有数据，避免 pandas 自动转换格式
                df = pd.read_excel(file, dtype=str)
            elif file.name.endswith('.csv'):
                df = pd.read_csv(file, dtype=str)
            else:
                messages.error(self.request, "文件格式不支持，请上传 .xlsx 或 .csv 文件。")
                return self.form_invalid(form)

            # 将 NaN 或 <NA> 等空值替换为空字符串
            df.fillna('', inplace=True)
            
            users_to_create = []
            students_to_create_data = []
            errors = []
            
            # 使用事务确保数据一致性
            with transaction.atomic():
                for index, row in df.iterrows():
                    row_num = index + 2
                    # 验证必填字段
                    required_fields = ['username', 'password', 'name', 'student_id_num', 'department_name', 'major_name']
                    if any(not str(row.get(field)).strip() for field in required_fields):
                        errors.append(f"第 {row_num} 行：缺少必填字段（用户名、密码、姓名、学号、院系、专业）。")
                        continue
                    
                    # 检查用户名和学号是否已存在
                    if User.objects.filter(username=row['username']).exists():
                        errors.append(f"第 {row_num} 行：用户名 '{row['username']}' 已存在。")
                        continue
                    if Student.objects.filter(student_id_num=row['student_id_num']).exists():
                        errors.append(f"第 {row_num} 行：学号 '{row['student_id_num']}' 已存在。")
                        continue
                    
                    # 获取外键对象
                    try:
                        department = Department.objects.get(dept_name=row['department_name'])
                        major = Major.objects.get(major_name=row['major_name'], department=department)
                    except Department.DoesNotExist:
                        errors.append(f"第 {row_num} 行：院系 '{row['department_name']}' 不存在。")
                        continue
                    except Major.DoesNotExist:
                         errors.append(f"第 {row_num} 行：在 '{row['department_name']}' 院系下找不到专业 '{row['major_name']}'。")
                         continue

                    # 准备创建 User 对象
                    user = User(username=row['username'], role=User.Role.STUDENT)
                    user.set_password(row['password']) # 直接设置加密后的密码
                    users_to_create.append(user)

                    # 准备创建 Student 的数据字典
                    student_data = {
                        'name': row['name'],
                        'student_id_num': row['student_id_num'],
                        'id_card': row.get('id_card', ''),
                        'gender': row.get('gender', '男'),
                        'department': department,
                        'major': major,
                        'birth_date': pd.to_datetime(row.get('birth_date')).date() if row.get('birth_date') else None,
                        'phone': row.get('phone', ''),
                    }
                    students_to_create_data.append(student_data)

                if errors: # 如果有任何解析错误，则立即回滚并显示错误
                     raise IntegrityError

                # 批量创建 User
                created_users = User.objects.bulk_create(users_to_create)

                # 将新创建的 user 关联到 student 数据上
                for i, user in enumerate(created_users):
                    students_to_create_data[i]['user'] = user

                # 批量创建 Student
                students_to_create = [Student(**data) for data in students_to_create_data]
                Student.objects.bulk_create(students_to_create)

            # 根据是否有错误显示不同的成功/警告消息
            if not errors:
                 messages.success(self.request, f"成功导入 {len(students_to_create)} 名学生！")
            else: # 这种情况理论上不会发生，因为有错误会触发回滚
                 for error in errors:
                    messages.warning(self.request, error)

        except IntegrityError:
             for error in errors:
                messages.error(self.request, error)
             messages.error(self.request, "导入失败，事务已回滚。请修正文件中的错误后重试。")
             # 出错后，重定向回导入页面，而不是学生列表
             return redirect('utils:student-bulk-import')
        
        except Exception as e:
            messages.error(self.request, f"处理文件时发生未知错误: {e}")
            return redirect('utils:student-bulk-import')

        return super().form_valid(form)

