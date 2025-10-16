# 系统包，
import datetime
import copy

# 第三方包，Dash是一个用于构建Web应用的Python框架
import dash
from dash import Input, Output, State, no_update, ALL

# 自定义模块，导入应用实例和数据库连接函数
from models.system.dept.dept_service import DeptService
from server import app, get_db, global_message, current_user
from models.system.service import PostService


# 构造岗位列表 返回数据格式
def render_post_list_table(
    posts: list | None, total_count: int | None, page_num: int = 1, page_size: int = 30
) -> tuple[list[dict], dict]:
    pagination = {
        "current": page_num,
        "pageSize": page_size,
        "total": total_count,
        # 显示分页大小切换器
        "showSizeChanger": True,
        "pageSizeOptions": [30, 50, 100],
    }
    if posts is None:
        return [], pagination
    post_data = [
        {
            "id": post.id,
            "key": str(post.id),
            "name": post.name,
            "post_code": post.post_code,
            "status": {"tag": "正常", "color": "cyan"}
            if post.status
            else {"tag": "停用", "color": "orange"},
            "dept_name": post.dept.name if post.dept else "无",
            # 直接返回布尔值
            "create_time": post.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "operation": [
                {"custom": "修改", "icon": "antd-edit"},
                {"custom": "删除", "icon": "antd-delete"},
            ],
        }
        for post in posts
    ]
    return post_data, pagination


@app.callback(
    [
        Output("post-list-table", "data"),
        Output("post-list-table", "pagination"),
        Output("post-dept-select", "treeData"),
    ],
    [
        Input("core-url", "pathname"),
    ],
)
def update_post_list_table(pathname):
    """页面初始化 加载数据库岗位数据"""
    if pathname == "/system/post":
        try:
            with get_db() as db:
                post_service = PostService(db, current_user_id=current_user.id)
                post_data, total_count = post_service.get_all(page=1, page_size=30)
                post_table_data, pagination = render_post_list_table(post_data, total_count)
                dept_options = DeptService(
                    db=db, current_user_id=current_user.id
                ).get_dept_tree_select()
            return post_table_data, pagination, dept_options
        except Exception as e:
            global_message("error", f"岗位列表加载失败:{e}")
    return no_update, no_update, no_update


# 查询岗位回调函
@app.callback(
    [
        Output("post-list-table", "data", allow_duplicate=True),
        Output("post-list-table", "pagination", allow_duplicate=True),
    ],
    [
        Input("post-search", "nClicks"),
        Input("post-reset", "nClicks"),
        Input("post-list-table", "pagination"),
        Input("post-refresh", "nClicks"),
        Input("post-modal", "okCounts"),
    ],
    [
        State("post-search-form", "values"),
    ],
    prevent_initial_call=True,
)
def post_list_select_data(
    search_nClicks, reset_click, pagination, refresh_click, okCounts, values
):
    values = values or {}
    page_num = pagination.get("current", 1)
    page_size = pagination.get("pageSize", 30)
    try:
        with get_db() as db:
            values = values or {}
            if dash.ctx.triggered_id == "post-search":
                values["status"] = True if values.get("status", 1) == 1 else False
                # 获取选择的部门id
                dept_ids = (
                    list(
                        DeptService(
                            db, current_user_id=current_user.id
                        ).get_descendant_dept_ids(set(values.get("dept_id", 1)))
                    )
                    if values.get("dept_id", None)
                    else None
                )
                values["dept_id"] = dept_ids
            post_data, total_count = PostService(
                db=db, current_user_id=current_user.id
            ).get_all_by_fields(page_num, page_size, **values)
        return render_post_list_table(post_data, total_count, page_num, page_size)
    except Exception as e:
        global_message("error", f"岗位查询失败:{e}")
    return dash.no_update
# 处理重置按钮清出搜索框值
@app.callback(
    Output("post-search-form", "values"),
    Input("post-reset", "nClicks"),
)
def reset_search_form(reset_click):
    return {}


# 处理新增 和 修改息
@app.callback(
    [
        Output("post-modal", "visible"),
        Output("post-modal", "title"),
        Output("post-modal-form", "values"),
        Output("post-delete-confirm-modal", "visible"),
        Output("post-delete-text", "children"),
        Output("post-delete-ids-store", "data"),
        Output("post-modal-from-dept-select", "treeData"),
    ],
    [
        Input({"type": "post-operation-button", "index": ALL}, "nClicks"),
        Input("post-list-table", "nClicksButton"),
    ],
    [
        State("post-list-table", "selectedRowKeys"),
        State("post-list-table", "recentlyClickedDropdownItemTitle"),
        State("post-list-table", "recentlyButtonClickedRow"),
        State("post-list-table", "clickedCustom"),
    ],
    prevent_initial_call=True,
)
def handle_post_operations(
    n_clicks, clicked_item, selected_keys, clicked_title, recent_row, clicked_custom
):
    """处理新增/修改弹窗"""
    trigger_id = dash.ctx.triggered_id
    if trigger_id in [
        {"index": "add", "type": "post-operation-button"},
        {"index": "edit", "type": "post-operation-button"},
        {"index": "delete", "type": "post-operation-button"},
        "post-list-table",
    ]:
        try:
            with get_db() as db:
                dept_options = DeptService(db, current_user.id).get_dept_tree_select()
        except Exception as e:
            global_message("error", f"岗位操作失败:{e}")
            return dash.no_update
        if trigger_id == {"index": "add", "type": "post-operation-button"}:
            return True, "新增岗位", None, False, None, None, dept_options
        if trigger_id == {"index": "edit", "type": "post-operation-button"} or (
            trigger_id == "post-list-table" and clicked_custom == "修改"
        ):
            if trigger_id == {"index": "edit", "type": "post-operation-button"}:
                post_id = int(selected_keys[0])
            else:
                post_id = recent_row["id"]
            try:
                with get_db() as db:
                    post = PostService(db, current_user.id).get(post_id)
                    return (
                        True,
                        "修改岗位",
                        {
                            "dept_id": post.dept_id,
                            "name": post.name,
                            "status": 1 if post.status else 0,
                            "post_code": post.post_code,
                            "remark": post.remark,
                        },
                        False,
                        None,
                        None,
                        dept_options,
                    )
            except Exception as e:
                global_message("error", f"岗位操作失败:{e}")
        if trigger_id == {"index": "delete", "type": "post-operation-button"} or (
            trigger_id == "post-list-table" and clicked_custom == "删除"
        ):
            if trigger_id == {"index": "delete", "type": "post-operation-button"}:
                return (
                    False,
                    None,
                    None,
                    True,
                    f"确定删除岗位编号为：{selected_keys}的岗位吗？",
                    [int(key) for key in selected_keys],
                    no_update,
                )

            else:
                return (
                    False,
                    None,
                    None,
                    True,
                    f"确定删除岗位：{recent_row['name']}？",
                    [recent_row["id"]],
                    no_update,
                )
    return no_update


# 新增修改 二次确认弹窗回调
@app.callback(
    [
        Output("post-modal", "visible", allow_duplicate=True),
        Output("post-modal-form", "values", allow_duplicate=True),
    ],
    [Input("post-modal", "okCounts")],
    [
        State("post-modal-form", "values"),
        State("post-modal", "title"),
        State("post-list-table", "recentlyButtonClickedRow"),
    ],
    prevent_initial_call=True,
)
def post_modal_confirm(okCounts, post_form_values, post_modal_title, recent_row):
    """岗位新增-修改，二次确认回调"""
    if not okCounts:
        return dash.no_update
    try:
        with get_db() as db:
            post_service = PostService(db, current_user.id)
            if dash.ctx.triggered_id == "post-modal" and post_modal_title == "新增岗位":
                return update_post_info(post_service, None, post_form_values)
            elif dash.ctx.triggered_id == "post-modal" and post_modal_title == "修改岗位":
                return update_post_info(
                    post_service, int(recent_row["id"]), post_form_values
                )
    except Exception as e:
        global_message("error", f"岗位操作失败:{e}")
    return dash.no_update


# 修改岗位 或者 创建岗位
def update_post_info(post_service, post_id, values):
    """
    修改岗位信息
    """
    if not values:
        global_message("error", "请填写表单数据")
        return True, dash.no_update

    required_fields = {
        "dept_id": "所属部门",
        "name": "岗位名称",
        "status": "状态",
        "post_code": "岗位编码",
    }
    required = [
        label
        for field, label in required_fields.items()
        if field not in values or not values[field]
    ]
    if required:
        global_message("error", f"请完善以下必填字段：{required}")
        return True, dash.no_update

    keys_to_remove = copy.deepcopy(values)
    for key, value in keys_to_remove.items():
        if value == "":
            values.pop(key)
        if post_id:
            post = post_service.update(post_id, **values)
            global_message("success", f"{post.name}岗位修改成功")
            return [False, None]
        else:
            # 新增创建人为当前用户，创建时间为当前时间
            values["create_by"] = current_user.id
            values["create_time"] = datetime.datetime.now()
            new_post = post_service.create(**values)
            global_message("success", f"岗位:[{new_post.name}]创建成功")
            return [False, None]


# 删除岗位
@app.callback(
    Input("post-delete-confirm-modal", "okCounts"),
    State("post-delete-ids-store", "data"),
    prevent_initial_call=True,
)
def delete_post(okCounts, delete_ids):
    if not okCounts:
        return dash.no_update, dash.no_update
    try:
        with get_db() as db:
            post_service = PostService(db, current_user.id)

            for post_id in delete_ids:
                # 调用删除方法
                result = post_service.delete(obj_id=post_id)
                if result:
                    global_message("success", f"{result.name}岗位删除成功")
            # 重新加载岗位列表数据
    except Exception as e:
        global_message("error", f"删除岗位信息失败{e}")



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
        Output("post-search-form-container", "hidden"),
        Output("post-hidden-tooltip", "title"),
    ],
    Input("post-hidden", "nClicks"),
    State("post-search-form-container", "hidden"),
    prevent_initial_call=True,
)

# 根据选择的表格数据行数控制删除按钮状态回调
app.clientside_callback(
    """
    (table_rows_selected) => {
        outputs_list = window.dash_clientside.callback_context.outputs_list;
        if (outputs_list) {
            if (table_rows_selected?.length > 0) {
                return false;
            }
            return true;
        }
        throw window.dash_clientside.PreventUpdate;
    }
    """,
    Output({"type": "post-operation-button", "index": "delete"}, "disabled"),
    Input("post-list-table", "selectedRowKeys"),
    prevent_initial_call=True,
)
