from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        """
        当App准备就绪时，导入并连接信号处理器。
        """
        import users.signals  # ✨