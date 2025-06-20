# users/management/commands/set_admin_role.py

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

# 获取您项目自定义的 User 模型
User = get_user_model()

class Command(BaseCommand):
    help = '将指定用户的角色设置为 ADMIN，并确保其为 is_staff 状态。'

    def add_arguments(self, parser):
        # 定义一个命令行参数，用于接收用户名
        parser.add_argument('username', type=str, help='需要设置为管理员角色的用户名')

    def handle(self, *args, **options):
        # 从命令行获取用户名
        username = options['username']
        try:
            # 查找用户
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'错误：用户 "{username}" 不存在。')

        # ✨ 关键：更新用户的 role 和 is_staff 字段
        user.role = User.Role.ADMIN  # 设置角色为 ADMIN
        user.is_staff = True         # 确保 is_staff 为 True，以便访问后台
        user.save()

        # 在终端打印成功消息
        self.stdout.write(self.style.SUCCESS(
            f'成功！用户 "{username}" 的角色已更新为 ADMIN。'
        ))

