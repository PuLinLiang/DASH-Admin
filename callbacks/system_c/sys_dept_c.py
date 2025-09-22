# 系统包
import datetime
import copy

# 第三方包
from dash import Input, Output, State
import dash

# 自定义包
from models.system.service import DeptService
from server import app, get_db, global_message, current_user


def get_dept_all_keys(nodes):
    """获取所有公司节点key,用展开部门节点"""
    keys = []
    for node in nodes:
        keys.append(node["key"])
    return keys


@app.callback(
    [
        Output("dept-list-table", "data"),
        Output("dept-list-table", "pagination"),
        Output("dept-list-table", "defaultExpandedRowKeys"),
    ],
    [
        Input("core-url", "pathname"),
        Input("dept-reset", "nClicks"),
        Input("dept-refresh", "nClicks"),
        Input("dept-delete-confirm-modal", "okCounts"),
        Input("dept-modal", "okCounts"),
    ],
)
def dep_list_url_data(
    pathname, reset_click, refresh_click, delete_modal_counts, modal_counts
):
    """
    用于初始化页面打开是加载部门数据和 展开节点
    """
    triggered_id = dash.ctx.triggered_id
    if (
        pathname == "/system/dept"
        or triggered_id == "dept-refresh"
        or triggered_id == "dept-reset"
        or triggered_id == "dept-delete-confirm-modal"
        or triggered_id == "dept-modal"
    ):
        try:
            with get_db() as db:
                service = DeptService(db, current_user_id=current_user.id)
                depts, total = service.get_all()
                dept_data = service._build_dept_tree(depts)
                defaul_dept_keys = get_dept_all_keys(dept_data)
                pagination = {
                    # 当前页码
                    "current": 1,
                    # 每页显示的记录数
                    "pageSize": 30,
                    # 总记录数
                    "total": total,
                    # 显示分页大小切换器
                    "showSizeChanger": True,
                    # 分页大小选项
                    "pageSizeOptions": [30, 50, 100],
                    # 显示快速跳转输入框
                    "showQuickJumper": True,
                }
                return [dept_data, pagination, defaul_dept_keys]
        except Exception as e:
            global_message("error", f"部门列表加载失败:{e}")
    return dash.no_update


app.clientside_callback(
    """
    (reset_click) => {
        if (reset_click) {
            return [ null, null]
        }
        return window.dash_clientside.no_update;
    }
    """,
    [
        Output("dept-dept_name-input", "value"),
        Output("dept-status-select", "value"),
    ],
    Input("dept-reset", "nClicks"),
    prevent_initial_call=True,
)

# 隐藏/显示用户搜索表单回调
app.clientside_callback(
    """
    (hidden_click, hidden_status) => {
        if (hidden_click) {
            return [
                !hidden_status,
                hidden_status ? '隐藏搜索' : '显示搜索'
            ]
        }
        return window.dash_clientside.no_update;
    }
    """,
    [
        Output("dept-search-form-container", "hidden"),
        Output("dept-hidden-tooltip", "title"),
    ],
    Input("dept-hidden", "nClicks"),
    State("dept-search-form-container", "hidden"),
    prevent_initial_call=True,
)


@app.callback(
    [
        Output("dept-list-table", "data", allow_duplicate=True),
        Output("dept-list-table", "pagination", allow_duplicate=True),
    ],
    [
        Input("dept-search", "nClicks"),
        Input("dept-list-table", "pagination"),
    ],
    [
        State("dept-dept_name-input", "value"),
        State("dept-status-select", "value"),
    ],
    prevent_initial_call=True,
)
# @dash_logger.log_operation("部门查询:{dept_name}{status}",action="部门.查询")
def dept_tree_search(search_nClicks, pagination, dept_name, status):
    """
    部门查询回调函数
    """
    # 分页参数处理，获取当前页码，默认为第1页
    page_num = pagination.get("current", 1)
    # 分页参数处理，获取每页显示的记录数，默认为30条
    page_size = pagination.get("pageSize", 30)
    try:
        with get_db() as db:
            # 初始查询条件
            kwargs = {}
            if dept_name:
                kwargs["name"] = dept_name
            if status is not None:
                kwargs["status"] = True if status == 1 else False
            dept_service = DeptService(db, current_user_id=current_user.id)
            dept_all, total_count = dept_service.get_all_by_fields(
                page_num, page_size, **kwargs
            )
            dept_data = dept_service._build_dept_tree(dept_all)
            new_pagination = {
                # 当前页码
                "current": page_num,
                # 每页显示的记录数
                "pageSize": page_size,
                # 总记录数
                "total": total_count,
                # 显示分页大小切换器
                "showSizeChanger": True,
                # 分页大小选项
                "pageSizeOptions": [30, 50, 100],
                # 显示快速跳转输入框
                "showQuickJumper": True,
            }
            return [dept_data, new_pagination]
    except Exception as e:
        global_message("error", f"部门查询失败:{e}")
    return dash.no_update


# 新建部门回调函数
@app.callback(
    Output("dept-modal", "visible"),
    Output("dept-modal", "title"),
    Output("dept-delete-confirm-modal", "visible"),
    Output("dept-tree-select", "treeData"),
    Output("dept-form", "values"),
    Output("dept-delete-text", "children"),
    [
        Input("dept-operation-button-add", "nClicks"),
        Input("dept-list-table", "nClicksButton"),
    ],
    [
        State("dept-list-table", "clickedContent"),
        State("dept-list-table", "recentlyButtonClickedRow"),
    ],
)
def show_add_modal(n_clicks, clicks_button, clicked_content, recent_row):
    """
    新增-修改-删除 功能实现函数
    """
    trigger_id = dash.ctx.triggered_id
    try:
        with get_db() as db:
            # 获取部门树数据，下拉菜单选择节点
            dept_tree_select = DeptService(db, current_user.id).get_dept_tree_select()
    except Exception as e:
        global_message("error", f"部门树加载失败:{e}")
        return dash.no_update
    if (
        trigger_id == "dept-list-table"
        and clicked_content == "新增"
        or trigger_id == "dept-operation-button-add"
    ):
        return True, "新增部门", False, dept_tree_select, None, None
    if trigger_id == "dept-list-table" and clicked_content == "修改":
        dept_from_data = {
            "id": recent_row["id"],
            "parent_id": recent_row["parent_id"],
            "name": recent_row["name"],
            "order_num": recent_row["order_num"],
            "status": 1,
        }
        return True, "修改部门", False, dept_tree_select, dept_from_data, None
    if trigger_id == "dept-list-table" and clicked_content == "删除":
        return (
            False,
            None,
            True,
            dept_tree_select,
            None,
            f"是否删除:{recent_row['name']}？",
        )

    return dash.no_update


# 新建部门表单提交回调函数
@app.callback(
    [
        Output("dept-modal", "visible", allow_duplicate=True),
        Output("dept-form", "values", allow_duplicate=True),
    ],
    [Input("dept-modal", "okCounts")],
    [
        State("dept-form", "values"),
        State("dept-modal", "title"),
        State("dept-list-table", "recentlyButtonClickedRow"),
    ],
    prevent_initial_call=True,
)
def handle_modal_callback_demo(
    okCounts, dept_form_values, dept_modal_title, recent_row
):
    if not okCounts:
        return dash.no_update
    try:
        with get_db() as db:
            dept_service = DeptService(db, current_user_id=current_user.id)
            if dash.ctx.triggered_id == "dept-modal" and dept_modal_title == "新增部门":
                return update_dept_info(None, dept_form_values, dept_service)

            elif dash.ctx.triggered_id == "dept-modal" and dept_modal_title == "修改部门":
                if dept_form_values.get("parent_id", None) == recent_row["id"]:
                    global_message("error", "上级部门不能选择自己")
                    return dash.no_update
                return update_dept_info(recent_row["id"], dept_form_values, dept_service)
    except Exception as e:
        global_message("error", f"修改部门信息失败{e}")
        return [True, dash.no_update]
    return dash.no_update


# 修改部门 或者 创建部门
def update_dept_info(dept_id, values, dept_service):
    """
    修改 / 新增 部门
    """
    if not values:
        global_message("error", "请填写表单数据")
        return dash.no_update

    required_fields = {
        "parent_id": "上级部门",
        "name": "部门名称",
        "order_num": "显示顺序",
        "status": "状态",
    }
    required = [
        label
        for field, label in required_fields.items()
        if field not in values or not values[field]
    ]
    if required:
        global_message("error", f"请完善以下必填字段：{required}")
        return dash.no_update

    keys_to_remove = copy.deepcopy(values)
    for key, value in keys_to_remove.items():
        if value == "":
            values.pop(key)


    if dept_id:
        dept = dept_service.update(dept_id, **values)
        global_message("success", f"{dept.name}修改部门信息成功")
        return [False, None]
    else:
        # 新增创建人为当前用户，创建时间为当前时间
        values["create_by"] = current_user.id
        values["create_time"] = datetime.datetime.now()
        new_dept = dept_service.create(**values)
        global_message("success", f"{new_dept.name}部门创建成功")
        return [False, None]



# 删除部门
@app.callback(
    Input("dept-delete-confirm-modal", "okCounts"),
    [State("dept-list-table", "recentlyButtonClickedRow")],
    prevent_initial_call=True,
)
def delete_dept(okCounts, recent_row):
    try:
        with get_db() as db:
            dept_service = DeptService(db, current_user.id)
            result = dept_service.delete(
                obj_id=recent_row["id"],
            )
            if result:
                global_message("success", f"{result.name}部门删除成功")
    except PermissionError as e:
        global_message("error", f"删除部门失败，权限不足:{e}")

    except Exception as e:
        global_message("error", f"删除部门失败{e}")
