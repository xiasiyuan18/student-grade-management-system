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
from .forms import StudentImportForm
from users.permissions import is_admin_or_teacher_or_manager


class StudentImportView(LoginRequiredMixin, FormView):
    template_name = "utils/student_import.html"
    form_class = StudentImportForm
    success_url = reverse_lazy("users:student-list")

    def dispatch(self, request, *args, **kwargs):
        if not (hasattr(request.user, 'is_authenticated') and request.user.is_authenticated and is_admin_or_teacher_or_manager(request.user)):
            messages.error(request, "您没有权限访问此页面。")
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        file = form.cleaned_data["file"]

        try:
            df = pd.read_excel(file)
            string_columns = ["username", "password", "name", "student_id_num", 
                            "department_name", "major_name", "minor_department_name", 
                            "minor_major_name", "gender", "phone", "id_card", 
                            "home_address", "dormitory"]
            
            for col in string_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).replace('nan', '')
                    
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
        success_count = 0
        
        for index, row in df.iterrows():
            row_num = index + 2
            try:
                # --- 获取和清理数据 ---
                def get_clean_value(row, key, default=""):
                    """获取并清理单元格值"""
                    value = row.get(key, default)
                    if pd.isna(value) or value == 'nan' or value == '':
                        return ""
                    return str(value).strip()

                username = get_clean_value(row, "username")
                password = get_clean_value(row, "password")
                name = get_clean_value(row, "name")
                student_id_num = get_clean_value(row, "student_id_num")
                department_name = get_clean_value(row, "department_name")
                major_name = get_clean_value(row, "major_name")
                
                # 处理 id_card 字段
                minor_department_name = get_clean_value(row, "minor_department_name")
                minor_major_name = get_clean_value(row, "minor_major_name")
                gender = get_clean_value(row, "gender", "男")
                phone = get_clean_value(row, "phone")
                id_card = get_clean_value(row, "id_card")
                home_address = get_clean_value(row, "home_address")
                dormitory = get_clean_value(row, "dormitory")

                # --- 数据校验 ---
                if not all([username, password, name, student_id_num, department_name, major_name]):
                    errors.append(f"第 {row_num} 行：必填字段不能为空。")
                    continue
                
                # 身份证号验证：确保身份证号唯一且格式正确
                if id_card:
                    # 验证身份证号格式
                    import re
                    if not re.match(r'^\d{17}[\dXx]$', id_card):
                        errors.append(f"第 {row_num} 行：身份证号 '{id_card}' 格式不正确，应为18位数字或17位数字+X。")
                        continue
                    
                    # 检查身份证号是否重复（只检查非空值）
                    if Student.objects.filter(id_card=id_card).exists():
                        errors.append(f"第 {row_num} 行：身份证号 '{id_card}' 已存在。")
                        continue
                
                # 检查用户名和学号是否已存在
                if CustomUser.objects.filter(username=username).exists():
                    errors.append(f"第 {row_num} 行：用户名 '{username}' 已存在。")
                    continue
                    
                if Student.objects.filter(student_id_num=student_id_num).exists():
                    errors.append(f"第 {row_num} 行：学号 '{student_id_num}' 已存在。")
                    continue

                # --- 查找院系和专业 ---
                try:
                    department = Department.objects.get(dept_name=department_name)
                except Department.DoesNotExist:
                    errors.append(f"第 {row_num} 行：主修院系 '{department_name}' 不存在。")
                    continue
                    
                try:
                    major = Major.objects.get(major_name=major_name, department=department)
                except Major.DoesNotExist:
                    errors.append(f"第 {row_num} 行：在 '{department_name}' 院系下找不到主修专业 '{major_name}'。")
                    continue

                # 处理辅修信息
                minor_major = None
                minor_department = None
                if minor_department_name and minor_major_name:
                    try:
                        minor_department = Department.objects.get(dept_name=minor_department_name)
                        minor_major = Major.objects.get(major_name=minor_major_name, department=minor_department)
                    except (Department.DoesNotExist, Major.DoesNotExist):
                        minor_major = None
                        minor_department = None
                
                # 处理出生日期
                birth_date_obj = None
                birth_date_val = row.get('birth_date')
                if pd.notna(birth_date_val):
                    try:
                        birth_date_obj = pd.to_datetime(birth_date_val, errors='coerce').date()
                        if pd.isna(birth_date_obj):
                            birth_date_obj = None
                    except:
                        birth_date_obj = None
                
                # --- 创建用户和学生档案 ---
                user = CustomUser.objects.create_user(
                    username=username, 
                    password=password, 
                    first_name=name,
                    role=CustomUser.Role.STUDENT
                )

                student_data = {
                    'user': user,
                    'student_id_num': student_id_num,
                    'name': name,
                    'major': major,
                    'department': department,
                    'gender': gender if gender else "男",
                    'birth_date': birth_date_obj,
                }
                
                if minor_major:
                    student_data['minor_major'] = minor_major
                if minor_department:
                    student_data['minor_department'] = minor_department
                if phone:
                    student_data['phone'] = phone
                if id_card:
                    student_data['id_card'] = id_card
                if home_address:
                    student_data['home_address'] = home_address
                if dormitory:
                    student_data['dormitory'] = dormitory
                
                Student.objects.create(**student_data)
                success_count += 1

            except Exception as e:
                errors.append(f"处理第 {row_num} 行时发生未知错误: {e}")
                continue

        # 错误处理
        if errors:
            transaction.set_rollback(True)
            messages.warning(self.request, f"导入过程中遇到 {len(errors)} 个错误，已回滚所有操作。")
            
            # 显示前5个错误
            for error in errors[:5]:
                messages.error(self.request, error)
            
            if len(errors) > 5:
                messages.error(self.request, f"还有 {len(errors) - 5} 个错误未显示...")
                
            return super().form_invalid(form)

        messages.success(self.request, f"学生批量导入成功！共导入 {success_count} 条记录。")
        return super().form_valid(form)
