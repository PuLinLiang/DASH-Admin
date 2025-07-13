import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style


def render():
    """子页面：首页渲染简单示例"""

    return fac.AntdSpace(
        fac.AntdAlert(
            type="warning",
            showIcon=True,
            message=f"这里是未开发页面",
            description="该页面尚未进行开发哦~",
        ),
        direction="vertical",
        style=style(width="100%"),
    )
