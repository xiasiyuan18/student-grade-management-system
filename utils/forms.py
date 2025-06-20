# utils/forms.py

from django import forms

# 将类名从 FileUploadForm 修改为 StudentImportForm
# 这样就和 views.py 中的导入语句匹配了
class StudentImportForm(forms.Form):
    """
    用于学生批量导入的文件上传表单。
    """
    file = forms.FileField(
        label='选择 Excel/CSV 文件',
        help_text='请确保文件格式与模板一致。',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

