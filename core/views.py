# core/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required # 如果首页需要登录才能访问，可以取消注释

# Create your views here.

# @login_required # 如果首页需要登录，取消此行注释，并确保settings.py中LOGIN_URL已配置
def home_view(request):
    """
    渲染前端的主页/仪表盘。
    """
    # 你可以在这里向模板传递一些上下文数据，如果首页需要的话
    # 例如，统计信息等
    context = {
        'page_title': '系统首页',
        # 'user_role': request.user.role if request.user.is_authenticated and hasattr(request.user, 'role') else None,
        # 更多上下文...
    }
    return render(request, 'home.html', context)

