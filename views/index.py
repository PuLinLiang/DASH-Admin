from dash import html
from .status_pages import _403
from flask_login import current_user

def render(*args, **kwargs):
    """
    系统首页视图函数
    返回包含基础布局的 HTML 结构
    """
    return html.Div(
        [
            html.H1(f"欢迎使用管理系统{current_user.name}"),
            html.P("请通过左侧导航栏选择功能模块"),
        ]
    )
