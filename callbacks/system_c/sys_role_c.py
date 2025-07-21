# 系统包，
import datetime
import copy

# 第三方包，Dash是一个用于构建Web应用的Python框架
import dash
from dash import Input, Output, State, no_update, ALL
import feffery_antd_components as fac

# 自定义模块，导入应用实例和数据库连接函数
from server import app, get_db, global_message, current_user
from tools.public.enum import DataScopeType, OperationType
from models.system.service import (
    RoleService,
    DeptService,
)
from models.system import RoleModel


# 构造角色列表 返回数据格式
def render_role_list_table(
    roles: list[RoleModel] | None,
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
    if roles is None:
        return [], pagination
    role_data = [
        {
            "id": role.id,
            "key": str(role.id),
            "role_key": role.role_key,
            "name": role.name,
            "status": {"tag": "正常", "color": "cyan"}
            if role.status
            else {"tag": "停用", "color": "orange"},
            "permissions": [
                {
                    "content": "查看",
                    "type": "primary",
                    "custom": {
                        "type": "查看角色权限",
                        "key": str(role.id),
                        "name": role.name,
                    },
                },
                {
                    "content": "设置",
                    "type": "primary",
                    "custom": {
                        "type": "设置角色权限",
                        "key": str(role.id),
                        "name": role.name,
                    },
                },
            ]
            if not role.is_admin
            else [],
            # "dept_name": [dept.name for dept in role.depts] if role.depts else "无",
            "create_time": role.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "operation": [
                {
                    "custom": {"type": "修改", "key": str(role.id), "name": role.name},
                    "icon": "antd-edit",
                },
                {
                    "custom": {"type": "删除", "key": str(role.id), "name": role.name},
                    "icon": "antd-delete",
                },
            ]
            if not role.is_admin
            else [],
        }
        for role in roles
    ]
    return role_data, pagination


@app.callback(
    [
        Output("role-list-table", "data"),
        Output("role-list-table", "pagination"),
        Output("role-dept-select", "treeData"),
    ],
    [
        Input("core-url", "pathname"),
    ],
)
def update_role_list_table(pathname):
    """页面初始化 加载数据库岗位数据"""
    if pathname == "/system/role":
        try:
            with get_db() as db:
                role_service = RoleService(db, current_user.id)
                role_data, total_count = role_service.get_all(1, 30)
                role_options = DeptService(
                    db=db, current_user_id=current_user.id
                ).get_dept_tree_select()
                role_table_data, pagination = render_role_list_table(
                    role_data, total_count
                )
            return role_table_data, pagination, role_options
        except Exception as e:
            global_message("error", f"更新失败: {str(e)}")
    return no_update, no_update, no_update


# 查询岗位回调函
@app.callback(
    [
        Output("role-list-table", "data", allow_duplicate=True),
        Output("role-list-table", "pagination", allow_duplicate=True),
    ],
    [
        Input("role-search", "nClicks"),
        Input("role-reset", "nClicks"),
        Input("role-list-table", "pagination"),
        Input("role-refresh", "nClicks"),
        Input("role-modal", "okCounts"),
    ],
    [
        State("role-search-form", "values"),
    ],
    prevent_initial_call=True,
)
def role_list_select_data(
    search_nClicks, reset_click, pagination, refresh_click, okCounts, values
):
    values = values or {}
    page_num = pagination.get("current", 1)
    page_size = pagination.get("pageSize", 30)
    try:
        with get_db() as db:
            role_service = RoleService(db, current_user.id)
            values = values or {}
            if dash.ctx.triggered_id == "role-search":
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
            role_data, total_count = role_service.get_all_by_fields(
                page_num, page_size, **values
            )
            return render_role_list_table(role_data, total_count, page_num, page_size)
    except Exception as e:
        global_message("error", f"查询失败: {str(e)}")
        return no_update, no_update


# 处理重置按钮清出搜索框值
@app.callback(
    Output("role-search-form", "values"),
    Input("role-reset", "nClicks"),
)
def reset_search_form(reset_click):
    return {}


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
        Output("role-search-form-container", "hidden"),
        Output("role-hidden-tooltip", "title"),
    ],
    Input("role-hidden", "nClicks"),
    State("role-search-form-container", "hidden"),
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
    Output({"type": "role-operation-button", "index": "delete"}, "disabled"),
    Input("role-list-table", "selectedRowKeys"),
    prevent_initial_call=True,
)


# 处理新增 和 修改息
@app.callback(
    [
        Output("role-modal", "visible"),
        Output("role-modal", "title"),
        Output("role-modal-form", "values"),
        Output("role-delete-confirm-modal", "visible"),
        Output("role-delete-text", "children"),
        Output("role-delete-ids-store", "data"),
        Output("role-modal-from-dept-select", "treeData"),
    ],
    [
        Input({"type": "role-operation-button", "index": ALL}, "nClicks"),
        Input("role-list-table", "nClicksButton"),
    ],
    [
        State("role-list-table", "selectedRowKeys"),
        State("role-list-table", "recentlyClickedDropdownItemTitle"),
        State("role-list-table", "recentlyButtonClickedRow"),
        State("role-list-table", "clickedCustom"),
    ],
    prevent_initial_call=True,
)
def handle_post_operations(
    n_clicks, clicked_item, selected_keys, clicked_title, recent_row, clicked_custom
):
    """处理新增/修改弹窗"""
    trigger_id = dash.ctx.triggered_id
    if trigger_id in [
        {"index": "add", "type": "role-operation-button"},
        {"index": "edit", "type": "role-operation-button"},
        {"index": "delete", "type": "role-operation-button"},
        "role-list-table",
    ]:
        try:
            with get_db() as db:
                dept_options = DeptService(db, current_user.id).get_dept_tree_select()
        except Exception as e:
            global_message("error", f"错误: {str(e)}")
        if trigger_id == {"index": "add", "type": "role-operation-button"}:
            return True, "新增角色", None, False, None, None, dept_options
        if trigger_id == {"index": "edit", "type": "role-operation-button"} or (
            trigger_id == "role-list-table" and clicked_custom["type"] == "修改"
        ):
            if trigger_id == {"index": "edit", "type": "role-operation-button"}:
                role_id = int(selected_keys[0])
            else:
                role_id = recent_row["id"]
            with get_db() as db:
                role = RoleService(db, current_user.id).get(role_id)
                return (
                    True,
                    "修改角色",
                    {
                        "dept_id": [int(dept.id) for dept in role.depts],
                        "name": role.name,
                        "role_key": role.role_key,
                        "status": int(role.status),
                        "remark": role.remark,
                    },
                    False,
                    None,
                    None,
                    dept_options,
                )
        if trigger_id == {"index": "delete", "type": "role-operation-button"} or (
            trigger_id == "role-list-table" and clicked_custom["type"] == "删除"
        ):
            if trigger_id == {"index": "delete", "type": "role-operation-button"}:
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
        Output("role-modal", "visible", allow_duplicate=True),
        Output("role-modal-form", "values", allow_duplicate=True),
    ],
    [Input("role-modal", "okCounts")],
    [
        State("role-modal-form", "values"),
        State("role-modal", "title"),
        State("role-list-table", "recentlyButtonClickedRow"),
    ],
    prevent_initial_call=True,
)
def role_modal_confirm(visible, role_form_values, role_modal_title, recent_row):
    """角色新增-修改，二次确认回调"""
    if not visible:
        return dash.no_update
    try:
        with get_db() as db:
            role_service = RoleService(db, current_user.id)
            dept_service = DeptService(db, current_user.id)
            if dash.ctx.triggered_id == "role-modal" and role_modal_title == "新增角色":
                return update_role_info(
                    role_service, dept_service, None, role_form_values
                )
            elif (
                dash.ctx.triggered_id == "role-modal" and role_modal_title == "修改角色"
            ):
                return update_role_info(
                    role_service, dept_service, int(recent_row["id"]), role_form_values
                )
            return dash.no_update
    except Exception as e:
        global_message("error", f"角色创建失败{e}")
        return [True, dash.no_update]


# 修改角色 或者 创建角色
def update_role_info(role_service, dept_service, role_id, values):
    """
    修改角色信息
    """
    if not values:
        global_message("error", "请填写表单数据")
        return [True, dash.no_update]

    required_fields = {
        "name": "角色名称",
        "status": "状态",
        "role_key": "角色字符",
    }
    required = [
        label
        for field, label in required_fields.items()
        if field not in values or not values[field]
    ]
    if required:
        global_message("error", f"请完善以下必填字段：{required}")
        return [True, dash.no_update]
    keys_to_remove = copy.deepcopy(values)
    for key, value in keys_to_remove.items():
        if value == "":
            values.pop(key)
    if role_id:
        diet_role = role_service.update(role_id, **values)
        global_message("success", f"{diet_role.name}角色修改成功")
        return [False, None]
    else:
        # 新增创建人为当前用户，创建时间为当前时间
        values["create_by"] = current_user.id
        values["create_time"] = datetime.datetime.now()
        values["data_scope_type"] = DataScopeType.DEPT
        new_role = role_service.create(**values)
        global_message("success", f"角色:[{new_role.name}]创建成功")
        return [False, None]


# 删除角色
@app.callback(
    Input("role-delete-confirm-modal", "okCounts"),
    State("role-delete-ids-store", "data"),
    prevent_initial_call=True,
)
def delete_role(okCounts, delete_ids):
    if not okCounts:
        return dash.no_update, dash.no_update
    try:
        with get_db() as db:
            role_service = RoleService(db=db, current_user_id=current_user.id)
            for role_id in delete_ids:
                # 调用删除方法
                result = role_service.delete(obj_id=role_id)
                global_message("success", f"{result.name}角色删除成功")
    except Exception as e:
        global_message("error", f"删除角色信息失败{e}")


def get_dept_all_keys(tree_data):
    """
    自动展开所有节点（当搜索时展开匹配路径）

    参数:
        tree_data: 部门树组件的数据

    返回:
        list: 展开节点的键列表，若无数据则返回dash.no_update
    """
    if tree_data:
        keys = []
        for node in tree_data:
            # 将当前节点的键添加到列表中
            keys.append(node["key"])
            if node.get("children"):
                # 递归调用函数，展开子节点
                keys.extend(get_dept_all_keys(node["children"]))
        return keys


def get_page_all_key(page_data):
    """获取页面数的所有key

    Args:
        page_data (list): 页面树组件的数据

    Returns:
        list: 页面数的所有key
    """
    if page_data:
        keys = []
        for node in page_data:
            # 将当前节点的键添加到列表中
            keys.append(node["title"])
        return keys
    return dash.no_update


@app.callback(
    [
        Output("role-permissions-modal", "visible", allow_duplicate=True),
        Output("role-form-permissions-modal-store", "data"),
        Output(
            "role-permissions-modal-form-custom_page_ids",
            "treeData",
            allow_duplicate=True,
        ),
        Output(
            "role-permissions-modal-form-custom_dept_ids",
            "treeData",
            allow_duplicate=True,
        ),
        Output(
            "role-permissions-modal-form-custom_dept_ids",
            "expandedKeys",
            allow_duplicate=True,
        ),
        Output(
            "role-permissions-modal-form-custom_dept_ids",
            "checkedKeys",
            allow_duplicate=True,
        ),
        Output(
            "role-permissions-modal-form-custom_page_ids",
            "checkedKeys",
            allow_duplicate=True,
        ),
        Output(
            "role-permissions-modal-form-page_action_ids",
            "children",
            allow_duplicate=True,
        ),
        Output("role-permissions-modal-form-page_action_ids", "values"),
        Output("role-permissions-modal", "title"),
        Output("role-permissions-modal-form-data_scope_type", "value"),
        Output("role-permissions-modal-form-data_scope_type", "options"),


    ],
    Input("role-list-table", "nClicksButton"),
    [
        State("role-list-table", "recentlyButtonClickedRow"),
        State("role-list-table", "clickedCustom"),
    ],
    prevent_initial_call=True,
)
def update_role_permissions(checked, row, custom):
    """更新角色权限"""
    if custom["type"] not in ["设置角色权限", "查看角色权限"]:
        return dash.no_update
    try:
        with get_db() as db:
            role_service = RoleService(db, current_user.id)
            dept_service = DeptService(db, current_user.id)

            role_id = int(custom["key"])  # 当前编辑角色 ＩＤ
            role = role_service.get(role_id)
            dept_tree = (
                dept_service.get_dept_tree()
            )  # 获取当前登录用户的权限范围内 部门ID 树
            if role is None:
                global_message("error", "角色不存在或无权限")
                return dash.no_update

            """ 获取当前编辑角色已有权限 """
            role_page_perms_action = {}  # 角色已有权限 页面-操作 映射
            role_page_ids = []  # 权限映射的页面树 页面列表

            def get_action_children(permission):
                """获取页面操作权限树"""
                perms_action = {}
                role_page = {}
                for per in permission:
                    perms_action[f"{per.page.name}-{per.page.url}"] = perms_action.get(
                        f"{per.page.name}-{per.page.url}", []
                    ) + [per.key]
                    if per.page.url not in role_page:
                        role_page[per.page.url] = {
                            "title": f"{per.page.name}-{per.page.url}",
                            "key": f"{per.page.name}-{per.page.url}",
                        }
                return list(role_page.values()), perms_action

            # 获取当前编辑角色信息
            role_page_ids, role_page_perms_action = get_action_children(
                role.permissions
            )
            if custom["type"] == "设置角色权限":
                """获取当前 登录用户权限范围内的权限页面 """
                user_permissions = role_service.get_user_permissions()
                role_page_ids, _ = get_action_children(user_permissions)
            if custom["type"] == "查看角色权限":
                """获取角色部门树"""
                dept_tree = role_service.get_role_dept_tree(role_id)

            dept_open_key = get_dept_all_keys(dept_tree)  # 部门树展开key
            checked_depts = [str(d) for d in role_service.get_role_dept_ids(role_id) ]  # 当前 编辑角色关联的部门id 用于选中部门树
            """ 根据当前用户角色范围类型,处理数据范围类型按渲染,和选中key"""
            data_scope_type_children=[]
            if current_user.data_scope_type == DataScopeType.DEPT_WITH_CHILD or current_user.is_admin:
                data_scope_type_children = [
                    {"label": "部门以下", "value": DataScopeType.DEPT_WITH_CHILD.code},
                    {"label": "本部门", "value": DataScopeType.DEPT.code},
                ]
            elif current_user.data_scope_type == DataScopeType.DEPT:
                data_scope_type_children = [
                    {"label": "本部门", "value": DataScopeType.DEPT.code},

                ]
            """ 获取当前角色范围类型"""
            data_scope_type = (
                role.data_scope_type.DEPT_WITH_CHILD.code
                if role.data_scope_type == DataScopeType.DEPT_WITH_CHILD
                else DataScopeType.DEPT.code
            )


            
            """根据当前角色操作权限 渲染操作配置按钮"""
            page_action_children = []
            for k, v in role_page_perms_action.items():
                action_children_options = []
                for per_key in v:
                    # 分割权限字符串获取操作类型编码，例如从'index:access'中提取'access'
                    _, op_code = per_key.split(":", 1)
                    # 获取对应的枚举实例
                    op_type = OperationType.get_by_code(op_code)
                    action_children_options.append(
                        {"label": op_type.description, "value": per_key}
                    )
                page_action_children.append(
                    fac.AntdFormItem(
                        fac.AntdCheckboxGroup(
                            name=k,  # 关键：使用页面URL作为表单字段名
                            options=action_children_options,
                        ),
                        label=f"{k}:操作权限",
                    )
                )

            # 构造返回值

            return [
                True,  # visible
                custom,  # store data
                role_page_ids,  # treeData (页面列表)
                dept_tree,  # 部门树
                dept_open_key,
                checked_depts,  # 部门选中项
                list(role_page_perms_action.keys()),  # 页面选中项 编辑角色现有权限页面
                page_action_children,  # 页面操作权限 勾选框渲染
                role_page_perms_action,  # 页面操作权限 勾选框选中
                custom.get("type", ""),  # 模态框标题
                data_scope_type,  # 数据范围类型
                data_scope_type_children,  # 数据范围类型 选项 options
            ]
    except Exception as e:
        global_message("error", f"角色权限获取失败{e}")
        return dash.no_update


# 角色配置模态框监听函数
@app.callback(
    [
        Output(
            "role-permissions-modal-form-custom_dept_ids",
            "treeData",
            allow_duplicate=True,
        ),
        Output(
            "role-permissions-modal-form-custom_page_ids",
            "treeData",
            allow_duplicate=True,
        ),
        Output(
            "role-permissions-modal-form-page_action_ids",
            "children",
            allow_duplicate=True,
        ),
        Output(
            "role-permissions-modal-form-custom_page_ids",
            "checkedKeys",
            allow_duplicate=True,
        ),
        Output(
            "role-permissions-modal-form-custom_dept_ids",
            "checkedKeys",
            allow_duplicate=True,
        ),
        Output(
            "role-permissions-modal-form-page_action_ids",
            "values",
            allow_duplicate=True,
        ),
        Output("role-permissions-modal-form-data_scope_type_button", "value",allow_duplicate=True),

        Output("role-permissions-modal-form-page_type", "value",allow_duplicate=True),

    ],
    [
        Input("role-permissions-modal-form-custom_dept_ids", "checkedKeys"),
        Input("role-permissions-modal-form-data_scope_type_button", "value"),
        Input("role-permissions-modal-form-data_scope_type", "value"),
        Input("role-permissions-modal-form-page_type", "value"),
        Input("role-permissions-modal-form-custom_page_ids", "checkedKeys"),
    ],
    [
        State("role-permissions-modal-form-page_action_ids", "children"),
        State("role-permissions-modal", "title"),
        State(
            "role-permissions-modal-form-custom_dept_ids",
            "treeData",
        ),
        State("role-permissions-modal-form-custom_page_ids", "treeData"),
        State("role-permissions-modal-form-custom_page_ids", "checkedKeys"),
        State("role-permissions-modal-form-page_action_ids", "values"),
    ],
    prevent_initial_call=True,
)
def role_permissions_modal_form_permissions_modal_store(
    dept_checkedkeys,  # 部门选中项
    data_scope_type_button,  # 角色数据范全选状态监控
    data_scope_type,  # 角色数据范围类型
    page_type,  # 页面访问权限，全选，取消
    page_in_checkedkeys,  # 页面树，选中 触发进来
    page_action_children,  # 页面操作权限，渲染的勾选框
    title,  # 模态框标题
    dept_treedata,  # 部门树数据
    page_treedata,  # 页面树
    page_checkedkeys,  # 页面树 选中key
    page_action_checkedkeys,  # 页面操作权限，选中项
):
    """角色配置模态框监听函数"""
    trigger_id = dash.ctx.triggered_id
    if title != "设置角色权限":
        return dash.no_update
    try:
        with get_db() as db:
            role_service = RoleService(db, current_user.id)
            data_scope_type_button_out=None
            page_type_out=None
            if data_scope_type_button == "all" and trigger_id=="role-permissions-modal-form-data_scope_type_button":
                """ 全选部门树 """
                dept_checkedkeys = get_dept_all_keys(dept_treedata)
                data_scope_type_button_out = "all"

            elif data_scope_type_button == "custom" and trigger_id=="role-permissions-modal-form-data_scope_type_button":
                dept_checkedkeys = []
                data_scope_type_button_out = "custom"


            """  获取当前登录用户的权限 用于操作权限赋权按钮渲染"""
            user_page_permissions = {}
            user_permissions = role_service.get_user_permissions()
            for u_perm in user_permissions:
                user_page_permissions[f"{u_perm.page.name}-{u_perm.page.url}"] = (
                    user_page_permissions.get(
                        f"{u_perm.page.name}-{u_perm.page.url}", []
                    )
                    + [u_perm.key]
                )

            def get_action_children(per_keys):
                """
                根据权限键列表生成操作子选项

                参数:
                    per_keys (list): 权限键列表

                返回:
                    list: 操作子选项列表
                """
                action_children_options = []
                for per_key in per_keys:
                    # 分割权限字符串获取操作类型编码，例如从'index:access'中提取'access'
                    _, op_code = per_key.split(":", 1)
                    # 获取对应的枚举实例
                    op_type = OperationType.get_by_code(op_code)
                    action_children_options.append(
                        {"label": op_type.description, "value": per_key}
                    )
                return action_children_options

            # 处理 页面树 全选 取消逻辑
            if (
                page_type == "all"
                and trigger_id == "role-permissions-modal-form-page_type"
            ):
                """ 渲染当前用户权限数据对应, 选择框"""
                page_action_children = []
                for k, v in user_page_permissions.items():
                    page_action_children.append(
                        fac.AntdFormItem(
                            fac.AntdCheckboxGroup(
                                name=k,  # 关键：使用页面URL作为表单字段名
                                options=get_action_children(v),
                            ),
                            label=f"{k}:操作权限",
                        )
                    )
                page_in_checkedkeys = get_page_all_key(page_treedata)  # 全选页面树
                page_action_children = (
                    page_action_children  # 渲染当前登录用户  全部权限选择框
                )
                page_action_checkedkeys = (
                    user_page_permissions  # 勾选当前登录用户 全部权限选择框
                )
                page_type_out = "all"
            elif (
                page_type == "none"
                and trigger_id == "role-permissions-modal-form-page_type"
            ):
                page_in_checkedkeys = []
                page_action_children = []
                page_action_checkedkeys = {}  # 取消勾选当前登录用户 全部权限选择框
                page_type_out = "none"
            """ 处理页面树 单选操作"""
            if dash.ctx.triggered_id == "role-permissions-modal-form-custom_page_ids":
                page_action_children = []
                page_action_children = [
                    fac.AntdFormItem(
                        fac.AntdCheckboxGroup(
                            name=check,  # 关键：使用页面URL作为表单字段名
                            options=get_action_children(user_page_permissions[check]),
                        ),
                        label=f"{check} :操作权限",
                    )
                    for check in page_in_checkedkeys
                ]
            page_action_checkedkeys = {
                k: v
                for k, v in page_action_checkedkeys.items()
                if k in page_in_checkedkeys
            }
            return [
                dept_treedata,
                page_treedata,
                page_action_children,  # 操作权限选择框 children
                page_in_checkedkeys,
                dept_checkedkeys,  # 部门树选中项
                page_action_checkedkeys,  # 操作权限选择框 values
                data_scope_type_button_out,
                page_type_out,
                
            ]
    except Exception as e:
        global_message("error", f"角色权限获取失败{e}")
    return dash.no_update


@app.callback(
    [
        Output("role-permissions-modal-form-data_scope_type_button", "readOnly"),
        Output("role-permissions-modal-form-data_scope_type", "readOnly"),
        Output("role-permissions-modal-form-page_type", "readOnly"),
        Output("role-permissions-modal-form-custom_page_ids", "readOnly"),
        Output("role-permissions-modal-form-page_action_ids", "readOnly"),
        Output("role-permissions-modal", "renderFooter"),
    ],
    Input("role-permissions-modal", "title"),
)
def set_permissions_modal_readonly(title):
    """
    查看角色 只读，禁止编辑
    """
    if title == "查看角色权限":
        return True,True, True, True, True, False  # 所有字段设为 disabled
    return False, False, False, False, False, True  # 可编辑状态


@app.callback(
    [
        Output("role-permissions-modal-form-data_scope_type_button", "value"),
        Output("role-permissions-modal-form-page_type", "value"),
    ],
    [
        Input("role-permissions-modal", "closeCounts"),
    ],
)
def role_permissions_modal_close(closecounts):
    """角色权限配置 关闭回调函数"""
    if closecounts:
        return None, None

    return dash.no_update


# 角色权限配置 确认回调函数
@app.callback(
    [
        Output("role-permissions-modal", "visible"),
    ],
    [
        Input("role-permissions-modal", "okCounts"),
    ],
    [
        State("role-permissions-modal-form-custom_dept_ids", "checkedKeys"),
        State("role-permissions-modal-form-page_action_ids", "values"),
        State("role-form-permissions-modal-store", "data"),
        State("role-permissions-modal-form-data_scope_type", "value"),
    ],
    prevent_initial_call=True,
)
def role_permissions_modal_form_confirm(
    okCounts, custom_dept_ids, page_action_ids, store_data,data_scope_type
):
    """角色权限配置 确认回调函数"""
    validations = [
        (not custom_dept_ids and not page_action_ids, "未配置角色权限"),
        (not custom_dept_ids and page_action_ids, "请选择角色数据范围"),
        (custom_dept_ids and not page_action_ids, "请配置角色 对应页面操作权限"),
    ]
    for condition, message in validations:
        if condition:
            global_message("error", message)
            return dash.no_update
    
    try:
        with get_db() as db:
            # 获取 store_data 里存入的角色ID,并且转换 int
            role_id = int(store_data.get("key"))
            role_service = RoleService(db=db, current_user_id=current_user.id)
            """ 获取权限字符集合 """
            per_keys = set()
            for per in page_action_ids.values():
                per_keys.update(per)
    
            # 调用服务层方法
            per_total, dept_total = role_service.configure_permissions(
                role_id=role_id,
                permission_keys=list(per_keys),
                dept_ids=custom_dept_ids,
                data_scope_type=DataScopeType.get_by_code(data_scope_type)
            )
            global_message(
                "success",
                f"角色权限配置成功,部门范围：{dept_total}个,权限范围：{per_total}个",
            )
            return [False]
    except Exception as e:
        global_message("error", f"角色权限配置失败{e}")
    return dash.no_update
