from django import forms

class StudentImportForm(forms.Form):
    """
    用于学生批量导入的文件上传表单。
    """
    file = forms.FileField(
        label='选择 Excel/CSV 文件',
        help_text='请确保文件格式与模板一致。',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

