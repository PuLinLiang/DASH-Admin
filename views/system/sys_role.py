import feffery_antd_components as fac
from dash import dcc, html
from callbacks.system_c import sys_role_c


# 角色前端页面
def render(*args, **kwargs):
    return [
        # 用于导出成功后重置dcc.Download的状态，防止多次下载文件
        dcc.Store(id="role-export-complete-judge-container"),
        # 绑定的导出组件
        dcc.Download(id="role-export-container"),
        # 角色管理模块操作类型存储容器
        dcc.Store(id="role-operations-store"),
        # 角色管理模块  角色权限配置存储容器
        dcc.Store(id="role-page-actions-store"),
        # 角色 权限配置 打开模态框角色id
        dcc.Store(id="role-form-permissions-modal-store"),
        # 角色管理模块删除操作行key存储容器
        dcc.Store(id="role-delete-ids-store"),
        fac.AntdRow(
            [
                fac.AntdCol(
                    [
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    html.Div(
                                        [
                                            fac.AntdForm(
                                                [
                                                    fac.AntdSpace(
                                                        [
                                                            fac.AntdFormItem(
                                                                fac.AntdInput(
                                                                    id="role-role_key-input",
                                                                    name="role_key",
                                                                    placeholder="请输入角色字符",
                                                                    autoComplete="off",
                                                                    allowClear=True,
                                                                    style={
                                                                        "width": 210
                                                                    },
                                                                ),
                                                                label="角色字符",
                                                            ),
                                                            fac.AntdFormItem(
                                                                fac.AntdInput(
                                                                    id="role-role_name-input",
                                                                    name="name",
                                                                    placeholder="请输入角色名称",
                                                                    autoComplete="off",
                                                                    allowClear=True,
                                                                    style={
                                                                        "width": 210
                                                                    },
                                                                ),
                                                                label="角色名称",
                                                            ),
                                                            fac.AntdFormItem(
                                                                fac.AntdSelect(
                                                                    name="status",
                                                                    options=[
                                                                        {
                                                                            "label": "正常",
                                                                            "value": 1,
                                                                        },
                                                                        {
                                                                            "label": "停用",
                                                                            "value": 0,
                                                                        },
                                                                    ],
                                                                    id="role-status-select",
                                                                    placeholder="角色状态",
                                                                    style={
                                                                        "width": 200
                                                                    },
                                                                ),
                                                                label="角色状态",
                                                            ),
                                                            fac.AntdFormItem(
                                                                fac.AntdTreeSelect(
                                                                    id="role-dept-select",
                                                                    treeDataMode="flat",
                                                                    treeData=[],
                                                                    name="dept_id",
                                                                    placeholder="请选择部门",
                                                                    style={
                                                                        "width": 200
                                                                    },
                                                                ),
                                                                label="所属部门",
                                                            ),
                                                            fac.AntdFormItem(
                                                                fac.AntdButton(
                                                                    "搜索",
                                                                    id="role-search",
                                                                    type="primary",
                                                                    icon=fac.AntdIcon(
                                                                        icon="antd-search"
                                                                    ),
                                                                )
                                                            ),
                                                            fac.AntdFormItem(
                                                                fac.AntdButton(
                                                                    "重置",
                                                                    id="role-reset",
                                                                    icon=fac.AntdIcon(
                                                                        icon="antd-sync"
                                                                    ),
                                                                )
                                                            ),
                                                        ],
                                                        style={"paddingBottom": "10px"},
                                                    ),
                                                ],
                                                layout="inline",
                                                enableBatchControl=True,
                                                id="role-search-form",
                                            )
                                        ],
                                        id="role-search-form-container",
                                        hidden=False,
                                    ),
                                )
                            ]
                        ),
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    fac.AntdSpace(
                                        [
                                            fac.AntdButton(
                                                [
                                                    fac.AntdIcon(icon="antd-plus"),
                                                    "新增",
                                                ],
                                                id={
                                                    "type": "role-operation-button",
                                                    "index": "add",
                                                },
                                                style={
                                                    "color": "#1890ff",
                                                    "background": "#e8f4ff",
                                                    "border-color": "#a3d3ff",
                                                },
                                            ),
                                            # if PermissionManager.check_perms(
                                            #     'system:post:add'
                                            # )
                                            # else [],
                                            fac.AntdButton(
                                                [
                                                    fac.AntdIcon(icon="antd-minus"),
                                                    "删除",
                                                ],
                                                id={
                                                    "type": "role-operation-button",
                                                    "index": "delete",
                                                },
                                                disabled=True,
                                                style={
                                                    "color": "#ff9292",
                                                    "background": "#ffeded",
                                                    "border-color": "#ffdbdb",
                                                },
                                            ),
                                            # if PermissionManager.check_perms(
                                            #     'system:post:remove'
                                            # )
                                            # else [],
                                            fac.AntdButton(
                                                [
                                                    fac.AntdIcon(
                                                        icon="antd-arrow-down"
                                                    ),
                                                    "导出",
                                                ],
                                                id="role-export",
                                                style={
                                                    "color": "#ffba00",
                                                    "background": "#fff8e6",
                                                    "border-color": "#ffe399",
                                                },
                                            ),
                                            # if PermissionManager.check_perms(
                                            #     'system:post:export'
                                            # )
                                            # else [],
                                        ],
                                        style={
                                            "paddingBottom": "10px",
                                        },
                                    ),
                                    span=16,
                                ),
                                fac.AntdCol(
                                    fac.AntdSpace(
                                        [
                                            html.Div(
                                                fac.AntdTooltip(
                                                    fac.AntdButton(
                                                        [
                                                            fac.AntdIcon(
                                                                icon="antd-search"
                                                            ),
                                                        ],
                                                        id="role-hidden",
                                                        shape="circle",
                                                    ),
                                                    id="role-hidden-tooltip",
                                                    title="隐藏搜索",
                                                )
                                            ),
                                            html.Div(
                                                fac.AntdTooltip(
                                                    fac.AntdButton(
                                                        [
                                                            fac.AntdIcon(
                                                                icon="antd-sync"
                                                            ),
                                                        ],
                                                        id="role-refresh",
                                                        shape="circle",
                                                    ),
                                                    title="刷新",
                                                )
                                            ),
                                        ],
                                        style={
                                            "float": "right",
                                            "paddingBottom": "10px",
                                        },
                                    ),
                                    span=8,
                                    style={"paddingRight": "10px"},
                                ),
                            ],
                            gutter=5,
                        ),
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    fac.AntdSpin(
                                        fac.AntdTable(
                                            id="role-list-table",
                                            columns=[
                                                {
                                                    "dataIndex": "id",
                                                    "title": "角色编号",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "name",
                                                    "title": "角色名称",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "role_key",
                                                    "title": "角色字符",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "title": "角色权限",
                                                    "dataIndex": "permissions",
                                                    "renderOptions": {
                                                        "renderType": "button",
                                                    },
                                                },
                                                {
                                                    "dataIndex": "status",
                                                    "title": "状态",
                                                    "renderOptions": {
                                                        "renderType": "tags"
                                                    },
                                                },
                                                # {
                                                #     "dataIndex": "dept_name",
                                                #     "title": "关联部门",
                                                #     "renderOptions": {
                                                #         "renderType": "ellipsis"
                                                #     },
                                                # },
                                                {
                                                    "dataIndex": "create_time",
                                                    "title": "创建日期",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "title": "操作",
                                                    "dataIndex": "operation",
                                                    "width": 170,
                                                    "renderOptions": {
                                                        "renderType": "button"
                                                    },
                                                },
                                            ],
                                            rowSelectionType="checkbox",
                                            rowSelectionWidth=50,
                                            bordered=True,
                                            mode="server-side",
                                            style={
                                                "width": "100%",
                                                "padding-right": "10px",
                                            },
                                        ),
                                        text="数据加载中",
                                    ),
                                )
                            ]
                        ),
                    ],
                    span=24,
                )
            ],
            gutter=5,
        ),
        # 新增和编辑角色表单modal
        fac.AntdModal(
            [
                fac.AntdForm(
                    [
                        fac.AntdFormItem(
                            fac.AntdTreeSelect(
                                id="role-modal-from-dept-select",
                                multiple=True,
                                treeDataMode="flat",
                                treeData=[],
                                name="dept_id",
                                placeholder="请选择部门",
                                style={"width": 350},
                            ),
                            required=True,
                            label="所属部门",
                        ),
                        fac.AntdFormItem(
                            fac.AntdInput(
                                name="name",
                                placeholder="请输入角色名称",
                                allowClear=True,
                                style={"width": 350},
                            ),
                            label="角色名称",
                            required=True,
                            hasFeedback=True,
                        ),
                        fac.AntdFormItem(
                            fac.AntdInput(
                                name="role_key",
                                placeholder="请输入角色字符",
                                allowClear=True,
                                style={"width": 350},
                            ),
                            label="角色字符",
                            required=True,
                            hasFeedback=True,
                        ),
                        fac.AntdFormItem(
                            fac.AntdRadioGroup(
                                name="status",
                                options=[
                                    {"label": "正常", "value": 1},
                                    {"label": "停用", "value": 0},
                                ],
                                defaultValue=1,
                            ),
                            label="角色状态",
                            required=True,
                            hasFeedback=True,
                        ),
                        fac.AntdFormItem(
                            fac.AntdInput(
                                name="remark",
                                placeholder="请输入内容",
                                allowClear=True,
                                mode="text-area",
                                style={"width": 350},
                            ),
                            label="备注",
                            hasFeedback=True,
                        ),
                    ],
                    id="role-modal-form",
                    enableBatchControl=True,
                    labelCol={"span": 6},
                    wrapperCol={"span": 18},
                )
            ],
            id="role-modal",
            mask=False,
            width=580,
            renderFooter=True,
            okClickClose=False,
        ),
        # 角色权限配置 modal
        fac.AntdModal(
            [
                fac.AntdRow(
                    [
                        fac.AntdCol(
                            fac.AntdCard(
                                [
                                    fac.AntdCol(
                                        fac.AntdFormItem(
                                            fac.AntdRadioGroup(
                                                options=[],
                                                id="role-permissions-modal-form-data_scope_type",
                                                name="data_scope_type",
                                                optionType="button",
                                                buttonStyle="solid",
                                                size="middle",
                                            ),
                                            label="范围类型：",
                                        ),
                                        style={"marginBottom": 10},
                                        span=24,
                                    ),
                                    # 部门选择 Tree 组件
                                    fac.AntdFormItem(
                                        fac.AntdTree(
                                            id="role-permissions-modal-form-custom_dept_ids",
                                            checkStrictly=True,
                                            treeData=[],
                                            multiple=True,
                                            checkable=True,
                                            nodeCheckedSuffix="🙂",
                                            style={"width": "100%"},
                                        ),
                                        label="关联部门：",
                                    ),
                                ],
                                title="数据范围设置",
                                extra=fac.AntdRadioGroup(
                                    options=[
                                        {"label": "全选", "value": "all"},
                                        {"label": "取消选择", "value": "none"},
                                    ],
                                    id="role-permissions-modal-form-data_scope_type_button",
                                    name="data_scope_type",
                                    optionType="button",
                                    buttonStyle="solid",
                                    size="middle",
                                ),
                                style={"height": "100%", "width": "100%"},
                            ),
                            style={
                                "height": "100%",
                                "margin": 0,
                                "padding": 15,
                                "overflow-y": "auto",
                            },
                            span=8,
                        ),
                        fac.AntdCol(
                            fac.AntdCard(
                                [
                                    # 页面选择 Tree 组件
                                    fac.AntdTree(
                                        id="role-permissions-modal-form-custom_page_ids",
                                        treeData=[],
                                        multiple=True,
                                        checkable=True,
                                        treeDataMode="flat",
                                        nodeCheckedSuffix="🙂",
                                    )
                                ],
                                title="权限对应页面",
                                extra=fac.AntdRadioGroup(
                                    options=[
                                        {"label": "全选", "value": "all"},
                                        {"label": "取消选择", "value": "none"},
                                    ],
                                    id="role-permissions-modal-form-page_type_button",
                                    name="page_type",
                                    optionType="button",
                                    buttonStyle="solid",
                                ),
                                style={
                                    "height": "100%",
                                    "width": "100%",
                                    "overflow-y": "auto",
                                },
                            ),
                            style={
                                "padding": 15,
                                "margin": 0,
                                "overflow-y": "auto",
                            },
                            span=8,
                        ),
                        fac.AntdCol(
                            fac.AntdCard(
                                fac.AntdForm(
                                    id="role-permissions-modal-form-page_action_ids",
                                    layout="vertical",
                                    enableBatchControl=True,
                                    values={},
                                ),
                                title="页面操作权限设置",
                                extra=fac.AntdRadioGroup(
                                    options=[
                                        {"label": "全选", "value": "all"},
                                        {"label": "取消选择", "value": "none"},
                                    ],
                                    id="role-permissions-modal-form-perminssions_type_button",
                                    name="data_scope_type",
                                    optionType="button",
                                    buttonStyle="solid",
                                    size="middle",
                                ),
                                style={
                                    "height": "100%",
                                    "width": "100%",
                                    "overflow-y": "auto",
                                },
                            ),
                            style={
                                "padding": 15,
                                "margin": 0,
                                "overflow-y": "auto",
                            },
                            span=8,
                        ),
                    ],
                    gutter=15,
                    style={"height": "600px"},
                )
            ],
            id="role-permissions-modal",
            mask=False,
            width="80%",
            renderFooter=True,
            okClickClose=False,
        ),
        # 删除岗位二次确认modal
        fac.AntdModal(
            fac.AntdText("是否确认删除？", id="role-delete-text"),
            id="role-delete-confirm-modal",
            visible=False,
            title="提示",
            renderFooter=True,
            centered=True,
        ),
    ]
