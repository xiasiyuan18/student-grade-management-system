# utils/forms.py

from django import forms

class FileUploadForm(forms.Form):
    """
    一个简单的文件上传表单。
    """
    file = forms.FileField(
        label='选择 Excel/CSV 文件',
        help_text='请确保文件格式与模板一致，支持 .xlsx 和 .csv 格式。',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
