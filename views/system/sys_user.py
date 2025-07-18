import feffery_antd_components as fac
from dash import dcc, html
from callbacks.system_c import sys_user_c


def render(*args, **kwargs):
    return [
        # 用于导出成功后重置dcc.Download的状态，防止多次下载文件
        dcc.Store(id="user-export-complete-judge-container"),
        # 绑定的导出组件
        dcc.Download(id="user-export-container"),
        # 用户管理模块操作类型存储容器
        dcc.Store(id="user-operations-store"),
        # 用户管理模块弹窗类型存储容器
        dcc.Store(id="user-modal_type-store"),
        # 用户管理模块表单数据存储容器
        dcc.Store(id="user-form-store"),
        # 用户管理模块删除操作行key存储容器
        dcc.Store(id="user-delete-ids-store"),
        dcc.Store(id="dept-tree-store"),  # 存储原始部门数据
        fac.AntdRow(
            [
                fac.AntdCol(
                    [
                        fac.AntdInput(
                            id="dept-input-search",
                            placeholder="请输入部门名称",
                            autoComplete="off",
                            allowClear=True,
                            prefix=fac.AntdIcon(icon="antd-search"),
                            style={"width": "85%"},
                        ),
                        fac.AntdTree(
                            id="dept-tree",
                            defaultExpandAll=True,
                            treeData=[],  # 初始化为空数组
                            defaultSelectedKeys=["1"],
                            style={"margin-top": "10px"},
                            highlightStyle={"background": "#ffffb8", "padding": 0},
                        ),
                    ],
                    span=4,
                ),
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
                                                                    id="user-user_name-input",
                                                                    name="name",
                                                                    placeholder="请输入用户昵称",
                                                                    autoComplete="off",
                                                                    allowClear=True,
                                                                    style={
                                                                        "width": 200
                                                                    },
                                                                ),
                                                                label="用户名",
                                                            ),
                                                            fac.AntdFormItem(
                                                                fac.AntdInput(
                                                                    id="user-phone_number-input",
                                                                    name="phone_number",
                                                                    placeholder="请输入手机号码",
                                                                    autoComplete="off",
                                                                    allowClear=True,
                                                                    style={
                                                                        "width": 200
                                                                    },
                                                                ),
                                                                label="手机号码",
                                                            ),
                                                            fac.AntdFormItem(
                                                                # 用户状态搜索选择框
                                                                fac.AntdSelect(
                                                                    id="user-status-select",
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
                                                                    placeholder="用户状态",
                                                                    style={
                                                                        "width": 200
                                                                    },
                                                                ),
                                                                label="用户状态",
                                                            ),
                                                        ],
                                                        style={"paddingBottom": "10px"},
                                                    ),
                                                    fac.AntdSpace(
                                                        [
                                                            fac.AntdFormItem(
                                                                fac.AntdDateRangePicker(
                                                                    id="user-create_time-range",
                                                                    name="create_time_range",
                                                                    showTime=True,
                                                                    needConfirm=True,
                                                                    style={
                                                                        "width": 200
                                                                    },
                                                                ),
                                                                label="创建时间",
                                                            ),
                                                            fac.AntdFormItem(
                                                                fac.AntdButton(
                                                                    "搜索",
                                                                    id="user-search",
                                                                    type="primary",
                                                                    icon=fac.AntdIcon(
                                                                        icon="antd-search"
                                                                    ),
                                                                )
                                                            ),
                                                            fac.AntdFormItem(
                                                                fac.AntdButton(
                                                                    "重置",
                                                                    id="user-reset",
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
                                                id="user-search-form",
                                            )
                                        ],
                                        id="user-search-form-container",
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
                                                    "type": "user-operation-button",
                                                    "index": "add",
                                                },
                                                style={
                                                    "color": "#1890ff",
                                                    "background": "#e8f4ff",
                                                    "border-color": "#a3d3ff",
                                                },
                                            ),
                                            # fac.AntdButton(
                                            #     [
                                            #         fac.AntdIcon(
                                            #             icon='antd-edit'
                                            #         ),
                                            #         '修改',
                                            #     ],
                                            #     id={
                                            #         'type': 'user-operation-button',
                                            #         'index': 'edit',
                                            #     },
                                            #     disabled=True,
                                            #     style={
                                            #         'color': '#71e2a3',
                                            #         'background': '#e7faf0',
                                            #         'border-color': '#d0f5e0',
                                            #     },
                                            # ),
                                            fac.AntdButton(
                                                [
                                                    fac.AntdIcon(icon="antd-minus"),
                                                    "删除",
                                                ],
                                                id={
                                                    "type": "user-operation-button",
                                                    "index": "delete",
                                                },
                                                disabled=True,
                                                style={
                                                    "color": "#ff9292",
                                                    "background": "#ffeded",
                                                    "border-color": "#ffdbdb",
                                                },
                                            ),
                                            fac.AntdButton(
                                                [
                                                    fac.AntdIcon(icon="antd-arrow-up"),
                                                    "导入",
                                                ],
                                                id="user-import",
                                                style={
                                                    "color": "#909399",
                                                    "background": "#f4f4f5",
                                                    "border-color": "#d3d4d6",
                                                },
                                            ),
                                            fac.AntdButton(
                                                [
                                                    fac.AntdIcon(
                                                        icon="antd-arrow-down"
                                                    ),
                                                    "导出",
                                                ],
                                                id="user-export",
                                                style={
                                                    "color": "#ffba00",
                                                    "background": "#fff8e6",
                                                    "border-color": "#ffe399",
                                                },
                                            ),
                                        ],
                                        style={"paddingBottom": "10px"},
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
                                                        id="user-hidden",
                                                        shape="circle",
                                                    ),
                                                    id="user-hidden-tooltip",
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
                                                        id="user-refresh",
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
                                            id="user-list-table",
                                            data=[],
                                            columns=[
                                                {
                                                    "dataIndex": "id",
                                                    "title": "用户编号",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "user_name",
                                                    "title": "用户名",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "name",
                                                    "title": "昵称",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "dept_name",
                                                    "title": "部门",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "post_name",
                                                    "title": "岗位",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "roles",
                                                    "title": "角色",
                                                    "renderOptions": {
                                                        "renderType": "tags"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "phonen",
                                                    "title": "手机号码",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "status",
                                                    "title": "状态",
                                                    "renderOptions": {
                                                        "renderType": "tags"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "create_time",
                                                    "title": "创建时间",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "title": "操作",
                                                    "dataIndex": "operation",
                                                    "renderOptions": {
                                                        "renderType": "dropdown",
                                                        "dropdownProps": {
                                                            "title": "更多"
                                                        },
                                                    },
                                                },
                                            ],
                                            rowSelectionType="checkbox",
                                            rowSelectionWidth=50,
                                            bordered=True,
                                            # pagination={},
                                            pagination={
                                                "current": 1,
                                                "pageSize": 30,
                                                "total": 30,
                                                "showSizeChanger": True,
                                                "pageSizeOptions": [30, 50, 100],
                                                "showQuickJumper": True,
                                            },
                                            mode="server-side",
                                            style={
                                                "width": "100%",
                                                "paddingRight": "10px",
                                            },
                                        ),
                                        text="数据加载中",
                                    ),
                                )
                            ]
                        ),
                    ],
                    span=20,
                ),
            ],
            gutter=5,
        ),
        # 新增和编辑用户表单modal
        fac.AntdModal(
            [
                fac.AntdForm(
                    [
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    fac.AntdFormItem(
                                        fac.AntdInput(
                                            name="name",
                                            placeholder="请输入用户昵称",
                                            allowClear=True,
                                            style={"width": "100%"},
                                        ),
                                        label="用户昵称",
                                        required=True,
                                        id={
                                            "type": "user-form-label",
                                            "index": "nick_name",
                                            "required": True,
                                        },
                                    ),
                                    span=12,
                                ),
                                fac.AntdCol(
                                    fac.AntdFormItem(
                                        fac.AntdTreeSelect(
                                            id="user-dpet-tree",
                                            name="dept_id",
                                            placeholder="请选择归属部门",
                                            treeDataMode="flat",
                                            treeData=[],
                                            treeNodeFilterProp="title",
                                            style={"width": "100%"},
                                        ),
                                        label="归属部门",
                                        required=True,
                                        id={
                                            "type": "user-form-label",
                                            "index": "dept_id",
                                            "required": False,
                                        },
                                    ),
                                    span=12,
                                ),
                            ],
                            gutter=10,
                        ),
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    fac.AntdFormItem(
                                        fac.AntdInput(
                                            name="phonenumber",
                                            placeholder="请输入手机号码",
                                            allowClear=True,
                                            style={"width": "100%"},
                                            maxLength=11,
                                        ),
                                        label="手机号码",
                                        id={
                                            "type": "user-form-label",
                                            "index": "phonenumber",
                                            "required": False,
                                        },
                                    ),
                                    span=12,
                                ),
                                fac.AntdCol(
                                    fac.AntdFormItem(
                                        fac.AntdInput(
                                            name="email",
                                            placeholder="请输入邮箱",
                                            allowClear=True,
                                            style={"width": "100%"},
                                        ),
                                        label="邮箱",
                                        id={
                                            "type": "user-form-label",
                                            "index": "email",
                                            "required": False,
                                        },
                                    ),
                                    span=12,
                                ),
                            ],
                            gutter=10,
                        ),
                        html.Div(
                            fac.AntdRow(
                                [
                                    fac.AntdCol(
                                        fac.AntdFormItem(
                                            fac.AntdInput(
                                                id="user-form-user_name",
                                                name="user_name",
                                                placeholder="请输入用户名",
                                                allowClear=True,
                                                style={"width": "100%"},
                                            ),
                                            label="用户名",
                                            required=True,
                                            id={
                                                "type": "user-form-label",
                                                "index": "user_name",
                                                "required": True,
                                            },
                                        ),
                                        span=12,
                                    ),
                                    fac.AntdCol(
                                        fac.AntdFormItem(
                                            fac.AntdInput(
                                                id="user-form-password",
                                                name="password_hash",
                                                placeholder="修改信息可以为空，新增必须填写",
                                                mode="password",
                                                passwordUseMd5=True,
                                                style={"width": "100%"},
                                            ),
                                            label="用户密码",
                                            required=True,
                                            id={
                                                "type": "user-form-label",
                                                "index": "password",
                                                "required": True,
                                            },
                                        ),
                                        span=12,
                                    ),
                                ],
                                gutter=10,
                            ),
                            id="user-user_name-password-container",
                        ),
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    fac.AntdFormItem(
                                        fac.AntdSelect(
                                            id="user-form-sex",
                                            name="sex",
                                            placeholder="请选择性别",
                                            options=[
                                                {"label": "男", "value": "男"},
                                                {"label": "女", "value": "女"},
                                                {"label": "未知", "value": "未知"},
                                            ],
                                            style={"width": "100%"},
                                        ),
                                        label="用户性别",
                                        id={
                                            "type": "user-form-label",
                                            "index": "sex",
                                            "required": False,
                                        },
                                    ),
                                    span=12,
                                ),
                                fac.AntdCol(
                                    fac.AntdFormItem(
                                        fac.AntdRadioGroup(
                                            id="user-form-status",
                                            name="status",
                                            options=[
                                                {"label": "正常", "value": 1},
                                                {"label": "停用", "value": 0},
                                            ],
                                            defaultValue=1,
                                        ),
                                        label="用户状态",
                                        id={
                                            "type": "user-form-label",
                                            "index": "status",
                                            "required": False,
                                        },
                                        required=True,
                                    ),
                                    span=12,
                                ),
                            ],
                            gutter=10,
                        ),
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    fac.AntdFormItem(
                                        fac.AntdSelect(
                                            id="user-post",
                                            name="post_id",
                                            placeholder="请选择岗位",
                                            options=[],
                                            # mode='multiple',
                                            optionFilterProp="label",
                                            style={"width": "100%"},
                                        ),
                                        label="岗位",
                                        required=True,
                                        id={
                                            "type": "user-form-label",
                                            "index": "post_ids",
                                            "required": False,
                                        },
                                    ),
                                    span=12,
                                ),
                                fac.AntdCol(
                                    fac.AntdFormItem(
                                        fac.AntdSelect(
                                            id="user-role",
                                            name="roles",
                                            placeholder="请选择角色",
                                            options=[],
                                            mode="multiple",  # 是否允许多选
                                            optionFilterProp="label",
                                            style={"width": "100%"},
                                        ),
                                        label="角色",
                                        # required=True,
                                        id={
                                            "type": "user-form-label",
                                            "index": "role_ids",
                                            "required": False,
                                        },
                                    ),
                                    span=12,
                                ),
                            ],
                            gutter=10,
                        ),
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    fac.AntdFormItem(
                                        fac.AntdInput(
                                            name="remark",
                                            placeholder="请输入内容",
                                            allowClear=True,
                                            mode="text-area",
                                            style={"width": "100%"},
                                        ),
                                        label="备注",
                                        id={
                                            "type": "user-form-label",
                                            "index": "remark",
                                            "required": False,
                                        },
                                        labelCol={"span": 4},
                                        wrapperCol={"span": 20},
                                    ),
                                    span=24,
                                ),
                            ],
                            gutter=10,
                        ),
                    ],
                    id="user-form",
                    enableBatchControl=True,
                    labelCol={"span": 8},
                    wrapperCol={"span": 16},
                    style={"marginRight": "15px"},
                )
            ],
            id="user-modal",
            mask=False,
            width=650,
            renderFooter=True,
            okClickClose=False,
        ),
        # 删除用户二次确认modal
        fac.AntdModal(
            fac.AntdText("是否确认删除？", id="user-delete-text"),
            id="user-delete-confirm-modal",
            visible=False,
            title="提示",
            renderFooter=True,
            centered=True,
        ),
        # 用户导入modal
        fac.AntdModal(
            [
                # html.Div(
                #     [
                #         ManuallyUpload(
                #             id='user-upload-choose', accept='.xls,.xlsx'
                #         ),
                #     ],
                #     style={'marginTop': '10px'},
                # ),
                html.Div(
                    [
                        fac.AntdCheckbox(id="user-import-update-check", checked=False),
                        fac.AntdText(
                            "是否更新已经存在的用户数据",
                            style={"marginLeft": "5px"},
                        ),
                    ],
                    style={"textAlign": "center", "marginTop": "10px"},
                ),
                html.Div(
                    [
                        fac.AntdText("仅允许导入xls、xlsx格式文件。"),
                        fac.AntdButton(
                            "下载模板",
                            id="download-user-import-template",
                            type="link",
                        ),
                    ],
                    style={"textAlign": "center", "marginTop": "10px"},
                ),
            ],
            id="user-import-confirm-modal",
            visible=False,
            title="用户导入",
            width=600,
            renderFooter=True,
            centered=True,
            okText="导入",
            okClickClose=False,
        ),
        fac.AntdModal(
            fac.AntdText(
                id="batch-result-content",
                className={"whiteSpace": "break-spaces"},
            ),
            id="batch-result-modal",
            visible=False,
            title="用户导入结果",
            renderFooter=False,
            centered=True,
        ),
        # # 重置密码modal
        # fac.AntdModal(
        #     [
        #         fac.AntdForm(
        #             [
        #                 fac.AntdFormItem(
        #                     fac.AntdInput(
        #                         id='reset-password-input', mode='password'
        #                     ),
        #                     label='请输入新密码',
        #                 ),
        #             ],
        #             layout='vertical',
        #         ),
        #         dcc.Store(id='reset-password-row-key-store'),
        #     ],
        #     id='user-reset-password-confirm-modal',
        #     visible=False,
        #     title='重置密码',
        #     renderFooter=True,
        #     centered=True,
        #     okClickClose=False,
        # ),
        # # 分配角色modal
        # fac.AntdModal(
        #     allocate_role.render(),
        #     id='user_to_allocated_role-modal',
        #     title='分配角色',
        #     mask=False,
        #     maskClosable=False,
        #     width=1000,
        #     renderFooter=False,
        #     okClickClose=False,
        # ),
    ]
