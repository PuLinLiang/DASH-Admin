from dash import set_props, no_update
import feffery_antd_components as fac
def global_message(mess_type, mess_content):
    """
    全局消息渲染
    """
    return set_props(
        "global-message",
        {
            "children": fac.AntdMessage(
                type=mess_type,
                content=mess_content,
            )
        },
    )