import feffery_antd_components as fac
from dash import dcc, html
from callbacks.system_c import sys_post_c


def render(*args, **kwargs):
    return [
        # 用于导出成功后重置dcc.Download的状态，防止多次下载文件
        dcc.Store(id="post-export-complete-judge-container"),
        # 绑定的导出组件
        dcc.Download(id="post-export-container"),
        # 岗位管理模块操作类型存储容器
        dcc.Store(id="post-operations-store"),
        # 岗位管理模块弹窗类型存储容器
        dcc.Store(id="post-modal_type-store"),
        # 岗位管理模块表单数据存储容器
        dcc.Store(id="post-form-store"),
        # 岗位管理模块删除操作行key存储容器
        dcc.Store(id="post-delete-ids-store"),
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
                                                                    id="post-post_id-input",
                                                                    name="post_code",
                                                                    placeholder="请输入岗位编号",
                                                                    autoComplete="off",
                                                                    allowClear=True,
                                                                    style={
                                                                        "width": 210
                                                                    },
                                                                ),
                                                                label="岗位编码",
                                                            ),
                                                            fac.AntdFormItem(
                                                                fac.AntdInput(
                                                                    id="post-post_name-input",
                                                                    name="name",
                                                                    placeholder="请输入岗位名称",
                                                                    autoComplete="off",
                                                                    allowClear=True,
                                                                    style={
                                                                        "width": 210
                                                                    },
                                                                ),
                                                                label="岗位名称",
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
                                                                    id="post-status-select",
                                                                    placeholder="岗位状态",
                                                                    style={
                                                                        "width": 200
                                                                    },
                                                                ),
                                                                label="岗位状态",
                                                            ),
                                                            fac.AntdFormItem(
                                                                fac.AntdTreeSelect(
                                                                    id="post-dept-select",
                                                                    treeDataMode='flat',
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
                                                                    id="post-search",
                                                                    type="primary",
                                                                    icon=fac.AntdIcon(
                                                                        icon="antd-search"
                                                                    ),
                                                                )
                                                            ),
                                                            fac.AntdFormItem(
                                                                fac.AntdButton(
                                                                    "重置",
                                                                    id="post-reset",
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
                                                id="post-search-form",
                                            )
                                        ],
                                        id="post-search-form-container",
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
                                                    "type": "post-operation-button",
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
                                                    "type": "post-operation-button",
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
                                                id="post-export",
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
                                                        id="post-hidden",
                                                        shape="circle",
                                                    ),
                                                    id="post-hidden-tooltip",
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
                                                        id="post-refresh",
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
                                            id="post-list-table",
                                            columns=[
                                                {
                                                    "dataIndex": "id",
                                                    "title": "岗位编号",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "name",
                                                    "title": "岗位名称",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "post_code",
                                                    "title": "岗位编码",
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
                                                    "dataIndex": "dept_name",
                                                    "title": "所属部门",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
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
        # 新增和编辑岗位表单modal
        fac.AntdModal(
            [
                fac.AntdForm(
                    [
                        fac.AntdFormItem(
                            fac.AntdTreeSelect(
                                id="post-modal-from-dept-select",
                                treeDataMode='flat',
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
                                placeholder="请输入岗位名称",
                                allowClear=True,
                                style={"width": 350},
                            ),
                            label="岗位名称",
                            required=True,
                            hasFeedback=True,
                        ),
                        fac.AntdFormItem(
                            fac.AntdInput(
                                name="post_code",
                                placeholder="请输入岗位编码",
                                allowClear=True,
                                style={"width": 350},
                            ),
                            label="岗位编码",
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
                            label="岗位状态",
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
                    id="post-modal-form",
                    enableBatchControl=True,
                    labelCol={"span": 6},
                    wrapperCol={"span": 18},
                )
            ],
            id="post-modal",
            mask=False,
            width=580,
            renderFooter=True,
            okClickClose=False,
        ),
        # 删除岗位二次确认modal
        fac.AntdModal(
            fac.AntdText("是否确认删除？", id="post-delete-text"),
            id="post-delete-confirm-modal",
            visible=False,
            title="提示",
            renderFooter=True,
            centered=True,
        ),
    ]
