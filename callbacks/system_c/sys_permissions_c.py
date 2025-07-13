# 系统包，
# 第三方包
import dash
from dash import Input, Output, State, no_update

# 自定义模块，导入应用实例和数据库连接函数
from server import app, get_db, global_message, current_user
from models.system.service import PermissionsService


# 构造列表 返回数据格式
def render_permissions_list_table(
    permissions: list | None,
    total_count: int | None,
    page_num: int = 1,
    page_size: int = 30,
) -> tuple[list[dict], dict]:
    pagination = {
        "current": page_num,
        "pageSize": page_size,
        "total": total_count,
        # 显示分页大小切换器
        "showSizeChanger": True,
        "pageSizeOptions": [30, 50, 100],
    }
    if permissions is None:
        return [], pagination
    permissions_data = [
        {
            "key": str(per.id),
            "name": per.name,
            "per_key": per.key,
            "status": {"tag": "正常", "color": "cyan"}
            if per.status
            else {"tag": "停用", "color": "orange"},
            # 直接返回布尔值
            "create_time": per.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for per in permissions
    ]
    return permissions_data, pagination


# @app.callback(
#     [
#         Output("permissions-list-table", "data"),
#         Output("permissions-list-table", "pagination"),
#     ],
#     [
#         Input("core-url", "pathname"),
#     ],
# )
# def update_permissions_list_table(pathname):
#     """页面初始化 加载数据库岗位数据"""
#     if pathname == "/system/permissions":
#         try:
#             with get_db() as db:
#                 permissions_service = PermissionsService(
#                     db, current_user_id=current_user.id
#                 )
#                 permissions_data, total_count = permissions_service.get_all(
#                     page=1, page_size=30
#                 )
#                 permissions_table_data, pagination = render_permissions_list_table(
#                     permissions_data, total_count
#                 )
#             return permissions_table_data, pagination
#         except Exception as e:
#             global_message("error", f"权限列表加载失败:{e}")
#     return dash.no_update

# 处理重置按钮清出搜索框值
@app.callback(
    Output("permissions-search-form", "values"),
    Input("permissions-reset", "nClicks"),
)
def reset_search_form(reset_click):
    return {}

# 查询回调函
@app.callback(
    [
        Output("permissions-list-table", "data", allow_duplicate=True),
        Output("permissions-list-table", "pagination", allow_duplicate=True),
    ],
    [
        Input("permissions-search", "nClicks"),
        Input("permissions-reset", "nClicks"),
        Input("permissions-list-table", "pagination"),
    ],
    [
        State("permissions-search-form", "values"),
    ],
    prevent_initial_call=True,
)
def permissions_list_select_data(search_nClicks, reset_click, pagination, values):
    values = values or {}
    page_num = pagination.get("current", 1)
    page_size = pagination.get("pageSize", 30)
    try:
        with get_db() as db:
            values = values or {}
            if not values:
                dash.no_update
            if dash.ctx.triggered_id == "permissions-search":
                values["status"] = True if values.get("status",1) == 1 else False
                if values.get("per_key", None):
                    values["key"] = values.get("per_key", None)
                    values.pop("per_key")
            if dash.ctx.triggered_id == "permissions-reset":
                values = {}
            permissions_data, total_count = PermissionsService(
                db=db, current_user_id=current_user.id
            ).get_all_by_fields(page_num, page_size, **values)
        return render_permissions_list_table(
            permissions_data, total_count, page_num, page_size
        )
    except Exception as e:
        global_message("error", f"岗位查询失败:{e}")
    return dash.no_update

