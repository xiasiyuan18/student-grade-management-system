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

            # ✨ 新增健壮性检查：检查列名是否存在
            if not all(col in df.columns for col in required_columns):
                missing_cols = ", ".join([col for col in required_columns if col not in df.columns])
                messages.error(self.request, f"文件格式错误：您的文件缺少必要的列: {missing_cols}。请下载并使用模板。")
                return redirect('utils:student-bulk-import')

            df.fillna('', inplace=True)
            
            users_to_create = []
            students_to_create_data = []
            errors = []
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    row_num = index + 2
                    if any(pd.isna(row.get(field)) or str(row.get(field)).strip() == '' for field in required_columns):
                        errors.append(f"第 {row_num} 行：缺少必填字段（用户名、密码、姓名、学号、院系、专业）。")
                        continue
                    
                    if User.objects.filter(username=row['username']).exists() or Student.objects.filter(student_id_num=row['student_id_num']).exists():
                        errors.append(f"第 {row_num} 行：用户名 '{row['username']}' 或学号 '{row['student_id_num']}' 已存在。")
                        continue
                    
                    try:
                        department = Department.objects.get(dept_name=row['department_name'])
                        major = Major.objects.get(major_name=row['major_name'], department=department)
                    except Department.DoesNotExist:
                        errors.append(f"第 {row_num} 行：院系 '{row['department_name']}' 不存在。")
                        continue
                    except Major.DoesNotExist:
                         errors.append(f"第 {row_num} 行：在 '{row['department_name']}' 院系下找不到专业 '{row['major_name']}'。")
                         continue

                    user = User(username=row['username'], role=User.Role.STUDENT)
                    user.set_password(row['password'])
                    users_to_create.append(user)

                    student_data = {
                        'name': row['name'], 'student_id_num': row['student_id_num'],
                        'id_card': row.get('id_card', ''), 'gender': row.get('gender', '男'),
                        'department': department, 'major': major,
                        'birth_date': pd.to_datetime(row.get('birth_date'), errors='coerce').date() if row.get('birth_date') else None,
                        'phone': row.get('phone', ''),
                    }
                    students_to_create_data.append(student_data)

                if errors:
                     raise IntegrityError("数据校验失败")

                created_users = User.objects.bulk_create(users_to_create)
                for i, user in enumerate(created_users):
                    students_to_create_data[i]['user'] = user

                students_to_create = [Student(**data) for data in students_to_create_data]
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
