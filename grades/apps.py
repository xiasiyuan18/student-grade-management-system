# grades/apps.py
from django.apps import AppConfig

class GradesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'grades'
    verbose_name = "成绩管理"

    def ready(self):
        # 确保信号被注册
        import grades.signals
