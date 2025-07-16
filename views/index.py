from dash import html
from .status_pages import _403
import feffery_antd_components as fac


def render(*args, **kwargs):
    """
    系统首页视图函数
    返回包含基础布局的 HTML 结构
    """
    if not current_user.check_permission("index:access"):
        return _403.render()
    return html.Div(
        [
            html.H1(f"欢迎使用管理系统{current_user.name}"),
            html.P("请通过左侧导航栏选择功能模块"),
        ]
    )
