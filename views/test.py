from dash import html
def render(*args, **kwargs):
    """
    系统首页视图函数
    返回包含基础布局的 HTML 结构
    """
    return html.Div(
        [
            html.P("测试页面"),
        ]
    )
