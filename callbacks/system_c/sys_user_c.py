# 系统包，
import copy  # 用于深拷贝对象
import datetime
import re

# 第三方包，Dash是一个用于构建Web应用的Python框架
import dash
from dash import Input, Output, State, no_update, ALL

# 用于获取当前登录用户信息
from flask_login import current_user

# 用于处理密码加密
from models.system.role.role_service import RoleService

# 自定义模块，导入应用实例和数据库连接函数
from models.system.service import DeptService, UserService, PostService
from server import app, get_db, global_message

# 自定义模块，导入系统相关的数据库模型


@app.callback(
    Output("dept-tree", "treeData"),  # 输出：部门树组件的数据
    Input("core-url", "pathname"),  # 输入：当前URL路径
)
def render_sys_users(pathname: str) -> list[dict] | None:
    """
    渲染系统用户管理页面的部门树数据

    功能说明:
    1. 当URL路径变化时触发

    参数:
        pathname: str - 当前页面URL路径，用于触发回调

    返回:
        List[Dict] - 部门树数据，格式示例:
        [
            {
                "title": "部门名称",
                "key": "部门ID",
                "children": [...]  # 子部门
            }
        ]

    异常处理:
        发生异常时返回空列表，确保前端组件正常渲染
    """
    # 仅当URL路径为系统用户管理页面时执行后续逻辑
    if pathname == "/system/user":
        try:
            # 获取数据库连接
            with get_db() as db:
                # 获取当前用户权限范围内的部门树数据
                dept = DeptService(db=db, current_user_id=current_user.id)
                dept_tree = dept.get_dept_tree()
                if not dept_tree:
                    return dash.no_update
                return dept_tree
        except Exception as e:
            global_message("error",f"部门树加载失败:{e}")
            # 异常时返回空列表，保证前端组件正常渲染
    return dash.no_update


"""
根据搜索值，显示对应的部门节点
"""
app.clientside_callback(
    """(value) => value""",
    Output("dept-tree", "searchKeyword"),
    Input("dept-input-search", "value"),
)


@app.callback(
    Output("dept-tree", "expandedKeys"),
    Input("dept-tree", "treeData"),
    prevent_initial_call=True,
)
def auto_expand_nodes(tree_data):
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
                keys.extend(auto_expand_nodes(node["children"]))
        return keys
    return dash.no_update


# 处理重置按钮清出搜索框值
@app.callback(
    Output("user-search-form", "values"),
    Input("user-reset", "nClicks"),
    prevent_initial_call=True,
)
def reset_dept_tree(n_clicks):
    """
    处理重置按钮清出搜索框值

    参数:
        n_clicks: 重置按钮的点击次数

    返回:
        list: 选中节点的键列表，若无数据则返回dash.no_update
    """
    if n_clicks:
        return None
    return dash.no_update


# 根据选择的表格数据行数控制修改按钮状态回调
app.clientside_callback(
    """
    (table_rows_selected) => {
        outputs_list = window.dash_clientside.callback_context.outputs_list;
        if (outputs_list) {
            if (table_rows_selected?.length === 1) {
                return false;
            }
            return true;
        }
        throw window.dash_clientside.PreventUpdate;
    }
    """,
    Output({"type": "user-operation-button", "index": "edit"}, "disabled"),
    Input("user-list-table", "selectedRowKeys"),
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
    Output({"type": "user-operation-button", "index": "delete"}, "disabled"),
    Input("user-list-table", "selectedRowKeys"),
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
        Output("user-search-form-container", "hidden"),
        Output("user-hidden-tooltip", "title"),
    ],
    Input("user-hidden", "nClicks"),
    State("user-search-form-container", "hidden"),
    prevent_initial_call=True,
)


@app.callback(
    [
        # 输出：用户列表表格的数据，允许重复更新
        Output("user-list-table", "data", allow_duplicate=True),
        # 输出：用户列表表格的分页信息，允许重复更新
        Output("user-list-table", "pagination", allow_duplicate=True),
    ],
    [
        # 输入：部门树组件中被选中的节点ID列表
        Input("dept-tree", "selectedKeys"),
        # 输入：搜索按钮的点击次数
        Input("user-search", "nClicks"),
        # 输入：重置按钮的点击次数
        Input("user-reset", "nClicks"),
        # 输入：用户列表表格的分页信息
        Input("user-list-table", "pagination"),
        # 输入：刷新按钮的点击次数
        Input("user-refresh", "nClicks"),
        # 输入：用户模态框的确认次数
        Input("user-modal", "okCounts"),
    ],
    [
        # 状态：用户搜索表单容器的隐藏状态
        State("user-search-form", "values"),
    ],
    prevent_initial_call=True,
)
def update_user_table(
    selected_keys,
    search_clicks,
    reset_clicks,
    pagination,
    refresh_clicks,
    user_modal_clicks,
    values,
):
    """
    表格数据回调函数，负责表格数据更新显示

    参数:
        selected_keys (list): 部门树组件中被选中的节点ID列表
        search_clicks (int): 搜索按钮的点击次数
        reset_clicks (int): 重置按钮的点击次数
        pagination (dict): 用户列表表格的分页信息
        refresh_clicks (int): 刷新按钮的点击次数
        user_modal_clicks (int): 用户模态框的确认次数
        values (dict): 搜索表单值

    返回:
        tuple: 包含用户列表表格数据和分页信息的元组
    """
    values = values or {}
    # 分页参数处理，获取当前页码，默认为第1页
    page_num = pagination.get("current", 1)
    # 分页参数处理，获取每页显示的记录数，默认为30条
    page_size = pagination.get("pageSize", 30)
    # 初始化部门id，初始值设为0
    dept_ids = []
    # 如果当前有选择的部门节点，就根据节点ID，查询他的子部门
    if selected_keys:
        try:
            with get_db() as db:
                # 获取选择的部门id
                dept_ids = (
                    list(
                        DeptService(
                            db, current_user_id=current_user.id
                        ).get_descendant_dept_ids(set(selected_keys))
                    )
                    if selected_keys
                    else []
                )
        except Exception as e:
            global_message("error",f"查询部门子节点失败:{e}")
    # 构建查询参数
    query_params = {}
    if dash.ctx.triggered_id != "user-reset":
        query_params = {
            # 用户姓名查询参数
            "name": values.get("name", None),
            # 用户电话号码查询参数
            "phonen": values.get("phone_number", None),
            # 用户状态查询参数
            "status": True if values.get("status", 1) == 1 else False,
            # 用户创建开始时间查询参数
            "create_time_start": values.get("create_time_range")[0]
            if values.get("create_time_range")
            else None,
            # 用户创建结束时间查询参数
            "create_time_end": values.get("create_time_range")[1]
            if values.get("create_time_range")
            else None,
            # 部门ID查询参数，避免传入空列表
            "dept_id": dept_ids if dept_ids else None,
        }
    # 使用字典推导式过滤空值
        query_params = {k: v for k, v in query_params.items() if v is not None}
    # 获取数据
    try:
        with get_db() as db:
        # 从数据库中获取符合条件的用户数据和总记录数
            users_data, total = UserService(
                db, current_user_id=current_user.id
            ).get_all_by_fields(
                page=page_num,
                page_size=page_size,
                **query_params,
            )
        # 构造分页参数
        new_pagination = {
            # 当前页码
            "current": page_num,
            # 每页显示的记录数
            "pageSize": page_size,
            # 总记录数
            "total": total,
            # 显示分页大小切换器
            "showSizeChanger": True,
            # 分页大小选项
            "pageSizeOptions": [30, 50, 100],
            # 显示快速跳转输入框
            "showQuickJumper": True,
        }
        if not users_data:
            return [], pagination
        # 构造返回数据
        table_data = [
            {
                # 用户ID
                "id": user.id,
                # 表格行的唯一标识
                "key": str(user.id),
                # 用户名
                "user_name": user.user_name,
                # 用户姓名
                "name": user.name,
                # 用户所在部门名称
                "dept_name": user.dept.name,
                # 用户岗位名称
                "post_name": user.post.name,
                # 用户角色列表
                "roles": [
                    {"tag": f"{role.name}", "color": "cyan"} for role in user.roles
                ],
                # 用户电话号码
                "phonen": user.phone or "无",
                # 用户状态，超级管理员状态不可修改
                "status": {"tag": "正常", "color": "cyan"}
                if user.status
                else {"tag": "停用", "color": "orange"},
                # 用户创建时间，格式化输出
                "create_time": user.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                # 操作按钮列表，超级管理员只有修改按钮
                "operation": [
                    {"title": "修改", "icon": "antd-edit"},
                    {"title": "删除", "icon": "antd-delete"},
                ]
                if user.id != 1
                else [],
            }
            for user in users_data
        ]

        return table_data, new_pagination
    except Exception as e:
            global_message("error",f"查询用户列表失败:{e}")
            users_data, total = [], 0

# 该回调函数根据不同的触发条件，控制多个组件的输出，包括模态框的显示、标题，部门树、角色和岗位的选项，删除确认信息等
@app.callback(
    [
        # 控制用户模态框的显示与隐藏
        Output("user-modal", "visible"),
        # 控制用户模态框的标题
        Output("user-modal", "title"),
        # 注意：此处可能存在拼写错误，推测应为"user-dept-tree"，为部门树组件提供数据，允许重复更新
        Output("user-dpet-tree", "treeData", allow_duplicate=True),
        # 为用户角色选择组件提供选项，允许重复更新
        Output("user-role", "options", allow_duplicate=True),
        # 为用户岗位选择组件提供选项，允许重复更新
        Output("user-post", "options", allow_duplicate=True),
        # 设置删除确认提示文本
        Output("user-delete-text", "children"),
        # 控制删除确认模态框的显示与隐藏
        Output("user-delete-confirm-modal", "visible"),
        # 存储待删除用户的ID
        Output("user-delete-ids-store", "data"),
        # 设置用户表单的默认值
        Output("user-form", "values"),
    ],
    [
        # 监听所有类型为"user-operation-button"的按钮点击次数
        Input({"type": "user-operation-button", "index": ALL}, "nClicks"),
        # 监听用户列表表格下拉菜单项的点击次数
        Input("user-list-table", "nClicksDropdownItem"),
    ],
    [
        # 获取用户列表表格中选中行的键
        State("user-list-table", "selectedRowKeys"),
        # 获取用户列表表格最近点击的下拉菜单项标题
        State("user-list-table", "recentlyClickedDropdownItemTitle"),
        # 获取用户列表表格最近点击下拉菜单项所在的行数据
        State("user-list-table", "recentlyDropdownItemClickedRow"),
        # 获取用户列表表格中选中的行数据
        State("user-list-table", "selectedRows"),
    ],
    # 防止初始调用
    prevent_initial_call=True,
)
def show_add_modal(
    n_clicks,
    nClicksDropdownItem,
    selected_row_keys,
    clicked_dropdown_item_title,
    recent_row,
    selected_rows,
):
    """
    新增-修改-删除 点击回调函数

    该函数根据触发的按钮或表格操作，控制模态框的显示、标题，以及填充表单数据等操作。

    参数:
        n_clicks (list): 所有类型为"user-operation-button"的按钮点击次数列表
        nClicksDropdownItem (int): 用户列表表格下拉菜单项的点击次数
        selected_row_keys (list): 用户列表表格中选中行的键列表
        clicked_dropdown_item_title (str): 用户列表表格最近点击的下拉菜单项标题
        recent_row (dict): 用户列表表格最近点击下拉菜单项所在的行数据
        selected_rows (list): 用户列表表格中选中的行数据列表

    返回:
        tuple: 包含多个组件输出值的元组，用于控制组件状态
    """
    # 获取触发回调的组件ID
    trigger_id = dash.ctx.triggered_id
    # 检查触发事件是否为新增、修改或删除操作
    if (
        trigger_id == {"index": "add", "type": "user-operation-button"}
        or trigger_id == {"index": "edit", "type": "user-operation-button"}
        or (trigger_id == "user-list-table" and clicked_dropdown_item_title == "修改")
        or trigger_id == {"index": "delete", "type": "user-operation-button"}
        or (trigger_id == "user-list-table" and clicked_dropdown_item_title == "删除")
    ):
        # 连接数据库
        try:    
            with get_db() as db:
            
                # 获取部门树数据，用于下拉菜单选择节点
                tree_data = DeptService(
                    db=db, current_user_id=current_user.id
                ).get_dept_tree_select()
                # 获取角色数据，用于下拉列表
                role_options = RoleService(
                    db=db, current_user_id=current_user.id
                ).get_options()
                # 获取岗位数据，用于下拉列表
                post_options = PostService(
                    db=db, current_user_id=current_user.id
                ).get_options()
        except Exception as e:
            global_message("error", f"失败:{e}")
            return dash.no_update
        if trigger_id == {"index": "add", "type": "user-operation-button"}:
            """ 处理新增用户操作 """
            # 返回组件输出值，显示新增用户模态框
            return (
                True,
                "新增用户",
                tree_data,
                role_options,
                post_options,
                None,
                None,
                None,
                None,
            )

        elif trigger_id == {"index": "edit", "type": "user-operation-button"} or (
            trigger_id == "user-list-table" and clicked_dropdown_item_title == "修改"
        ):
            """处理修改用户操作"""
            # 初始化用户ID
            user_id = 0
            if trigger_id == {"index": "edit", "type": "user-operation-button"}:
                # 从选中行的键中获取用户ID
                user_id = int(selected_row_keys[0])
            elif (
                trigger_id == "user-list-table"
                and clicked_dropdown_item_title == "修改"
            ):
                # 从最近点击的行数据中获取用户ID
                user_id = int(recent_row["id"])
            # 从数据库中获取用户信息
            
            try:
                with get_db() as db:
                    user = UserService(db=db, current_user_id=current_user.id).get(user_id)
                    # 设置用户表单的默认值
                    default_values = {
                        "name": user.name ,
                        "dept_id": user.dept_id,
                        "phone": user.phone,
                        "email": user.email,
                        "user_name": user.user_name,
                        "password_hash": "",
                        "sex": user.sex,
                        "status": 1 if user.status else 0,
                        "post_id": user.post_id,
                        "roles": [role.id for role in user.roles],
                        "remark": user.remark,
                    }

                    # 返回组件输出值，显示修改用户模态框并填充表单数据
                    return (
                        True,
                        "修改用户",
                        tree_data,
                        role_options,
                        post_options,
                        None,
                        None,
                        None,
                        default_values,
                    )
            except Exception as e:
                global_message("error", f"获取用户信息失败:{e}")
                return dash.no_update
        # 处理删除用户操作
        elif trigger_id == {"index": "delete", "type": "user-operation-button"} or (
            trigger_id == "user-list-table" and clicked_dropdown_item_title == "删除"
        ):
            if trigger_id == {"index": "delete", "type": "user-operation-button"}:
                # 检查是否包含超级管理员ID
                if "1" in selected_row_keys:
                    # 若包含超级管理员ID，提示不能删除
                    return [
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        None,
                        "不能删除超级管理员",
                        True,
                        None,
                        None,
                    ]
                # 提示确认删除信息并存储待删除用户ID
                return [
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    None,
                    f"是否确认删除用户编号为{selected_row_keys}的用户？",
                    True,
                    [int(s) for s in selected_row_keys],
                    None,
                ]
            
            elif (
                trigger_id == "user-list-table"
                and clicked_dropdown_item_title == "删除"
            ):
                # 检查是否为超级管理员ID
                if recent_row["id"] == 1:
                    # 若为超级管理员ID，提示不能删除
                    return [
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        None,
                        "不能删除超级管理员",
                        True,
                        None,
                        None,
                    ]
                # 提示确认删除信息并存储待删除用户ID
                return [
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    None,
                    f"是否确认删除用户编号为{recent_row['id']}的用户？",
                    True,
                    [recent_row["id"]],
                    None,
                ]


# 删除 新增 修改，二次确认回调函数
@app.callback(
    [
        Output("user-modal", "visible", allow_duplicate=True),
        Output("user-list-table", "selectedRowKeys"),
        Output("user-list-table", "recentlyClickedDropdownItemTitle"),
        Output("user-list-table", "recentlyDropdownItemClickedRow"),
        Output("user-list-table", "selectedRows"),
    ],
    [
        Input("user-modal", "okCounts"),
    ],
    [
        State("user-modal", "title"),
        State("user-form", "values"),
        State("user-list-table", "selectedRowKeys"),
        State("user-list-table", "recentlyClickedDropdownItemTitle"),
        State("user-list-table", "recentlyDropdownItemClickedRow"),
        State("user-list-table", "selectedRows"),
    ],
    prevent_initial_call=True,
)
def handle_modal_callback_demo(
    okCounts,
    title,
    values,
    selected_row_keys,
    clicked_dropdown_item_title,
    recent_row,
    selected_rows,
):
    """
    新增用户信息-修改用户信息：对话框确认后数据操作逻辑
    """
    if okCounts is None:
        return no_update
    with get_db() as db:
        user_id = recent_row["id"] if title == "修改用户" else None
        return update_user_info(db, user_id, values)


# 修改用户信息
def update_user_info(db, user_id, values):
    """
    修改用户信息
    """
    if not values:
        global_message("error", "请填写表单数据")
        return dash.no_update
    required_fields = {
        "user_name": "用户名",
        "password_hash": "用户密码",
        "name": "用户昵称",
        "post_id": "岗位",
        # "roles": "角色",
        "status": "用户状态",
        "dept_id": "归属部门",
    }
    if user_id:
        required_fields.pop("password_hash")
    required = [
        label
        for field, label in required_fields.items()
        if field not in values
        or (
            values[field] is None  # 处理None值
            or (
                isinstance(values[field], str) and values[field].strip() == ""
            )  # 处理空字符串
            or (
                not isinstance(values[field], (int, float)) and not values[field]
            )  # 处理非数字类型的假值
        )
    ]
    if required:
        global_message("error", f"请完善以下必填字段：{required}")
        return dash.no_update
    # 检查用户名是否存在
    user_name = UserService.get_user_by_username(db, values["user_name"])
    print(values["user_name"])
    print(user_name.__dict__)
    if user_name and user_name.id != user_id:
        global_message("error", "用户名已存在")
        return no_update
        # 移除值为空的键
    keys_to_remove = copy.deepcopy(values)
    for key, value in keys_to_remove.items():
        if value == "":
            values.pop(key)
        elif key == "password_hash" and value != "":
            try:
                values["password_hash"] = UserService(
                    db=db, current_user_id=current_user.id
                ).create_password_hash(values["password_hash"])
            except Exception as e:
                global_message("error", f"密码格式错误：{e}")
                return no_update
    # 检查手机号码格式
    phonenumber = values.get("phonenumber")
    # 检查邮箱格式
    email = values.get("email")
    # 手机号验证正则
    PHONE_REGEX = re.compile(r"^1[3-9]\d{9}$")
    # 邮箱验证正则
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    # 在验证部分改为：
    if phonenumber and not PHONE_REGEX.match(phonenumber):
        global_message("error", "手机号格式不正确")
        return no_update

    if email and not EMAIL_REGEX.match(email):
        global_message("error", "邮箱格式不正确")
        return no_update
    # 获取新角色ID
    new_role_id = values.get("roles")
    # 移除roles键
    values.pop("roles", None)
    
    
    try:
        if user_id:
            user = UserService(db=db, current_user_id=current_user.id).update(
                user_id, **values
            )
            user.roles=[]
            roles, _ = RoleService(
                db=db, current_user_id=current_user.id
            ).get_all_by_fields(id=new_role_id)
            if roles:
                user.roles = roles
            global_message("success", f"{user.name}修改用户信息成功")
            return [False, no_update, no_update, no_update, no_update]
        else:
            # 新增创建人为当前用户，创建时间为当前时间
            values["create_by"] = current_user.id
            values["create_time"] = datetime.datetime.now()
            new_user = UserService(db=db, current_user_id=current_user.id).create(
                **values
            )
            roles, _ = RoleService(
                db=db, current_user_id=current_user.id
            ).get_all_by_fields(id=new_role_id)
            if roles:
                new_user.roles = roles
            global_message("success", f"{new_user.name}用户创建成功")
            return [False, no_update, no_update, no_update, no_update]
    except Exception as e:
        global_message("error", f"失败:{e}")
        return [True, no_update, no_update, no_update, no_update]


@app.callback(
    Input("user-delete-confirm-modal", "okCounts"),
    State("user-delete-ids-store", "data"),
    prevent_initial_call=True,
)
def user_delete_confirm(delete_confirm, user_ids_data):
    """
    删除用户弹窗确认回调，实现删除操作
    """
    if delete_confirm:
        
        try:
            with get_db() as db:
                for user_id in user_ids_data:
                    result = UserService(db=db, current_user_id=current_user.id).delete(
                        user_id
                    )
                    if result:
                        global_message("success", f"用户{result.name}删除成功")
        except PermissionError as e:
            global_message("error", f"删除用户失败，权限不足:{e}")
            return None
        except Exception as e:
            global_message("error", f"删除用户失败{e}")
            return None
    return None
