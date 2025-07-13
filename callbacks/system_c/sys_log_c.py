# 第三方包
import dash
from dash import Input, Output, State

# 自定义模块，导入应用实例和数据库连接函数
from server import app, get_db, global_message, current_user
from models.system.syslog.logs_server import LogService

# 构造列表 返回数据格式
def render_log_list_table(
    logs: list | None,
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
    if logs is None:
        return [], pagination
    logs_data = [
        {
            "key": str(log.id),
            "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if log.timestamp
            else "无",
            "log_level": log.log_level,
            "message": log.message,
            "logmodule": log.logmodule,
            "operation": log.operation,
            "logmodule_operation": log.logmodule_operation,
            "status": log.status,
            "duration_ms": log.duration_ms,
            # "ip": log.ip,
            "description": str(log.description),
        }
        for log in logs
    ]
    return logs_data, pagination

@app.callback(
    Output("log-search-form", "values"),
    Input("log-reset", "nClicks"),
)
def reset_search_form(reset_click):
    return {}

@app.callback(
    [
        Output("log-list-table", "data"),
        Output("log-list-table", "pagination"),
    ],
    [
        Input("core-url", "pathname"),
    ],
)
def update_log_list_table(pathname):
    """页面初始化 加载日志数据"""
    if pathname == "/system/log":
        try:
            with get_db() as db:
                log_service = LogService(db_session=db)
                logs_data, total_count = log_service.get_all_by_fields(
                    page=1, page_size=30
                )
                logs_table_data, pagination = render_log_list_table(
                    logs_data, total_count
                )
            return logs_table_data, pagination
        except Exception as e:
            global_message("error", f"日志列表加载失败:{e}")
    return dash.no_update

# 查询回调函
@app.callback(
    [
        Output("log-list-table", "data", allow_duplicate=True),
        Output("log-list-table", "pagination", allow_duplicate=True),
    ],
    [
        Input("log-search", "nClicks"),
        Input("log-reset", "nClicks"),
        Input("log-list-table", "pagination"),
    ],
    [
        State("log-search-form", "values"),
    ],
    prevent_initial_call=True,
)
def log_list_select_data(search_nClicks, reset_click, pagination, values):
    values = values or {}
    page_num = pagination.get("current", 1)
    page_size = pagination.get("pageSize", 30)
    try:
        with get_db() as db:
            values = values or {}
            if not values:
                dash.no_update  
            if dash.ctx.triggered_id == "log-reset":
                values = {}
            if values.get("create_time_range", None):
                values["create_time_start"] = values["create_time_range"][0]
                values["create_time_end"] = values["create_time_range"][1]
            log_service = LogService(db_session=db)
            logs_data, total_count = log_service.get_all_by_fields(
                page=page_num,
                page_size=page_size,
                **values
            )
        return render_log_list_table(logs_data, total_count, page_num, page_size)
    except Exception as e:
        global_message("error", f"查询失败:{e}")
    return dash.no_update