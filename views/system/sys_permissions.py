import feffery_antd_components as fac
from dash import dcc, html
import feffery_utils_components as fuc
from callbacks.system_c import sys_permissions_c


def render(*args, **kwargs):
    return [
        # 权限管理模块操作类型存储容器
        dcc.Store(id="permissions-operations-store"),
        # 权限管理模块弹窗类型存储容器
        dcc.Store(id="permissions-modal_type-store"),
        # 权限管理模块修改操作行key存储容器
        dcc.Store(id="permissions-edit-id-store"),
        # 权限管理模块删除操作行key存储容器
        dcc.Store(id="permissions-delete-ids-store"),
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
                                                    fac.AntdFormItem(
                                                        fac.AntdInput(
                                                            id="permissions-name-input",
                                                            name="name",
                                                            placeholder="请输入权限名称",
                                                            autoComplete="off",
                                                            allowClear=True,
                                                            style={"width": 240},
                                                        ),
                                                        label="权限名称",
                                                        style={"paddingBottom": "10px"},
                                                    ),
                                                    fac.AntdFormItem(
                                                        fac.AntdInput(
                                                            id="permissions-key-input",
                                                            name="key",
                                                            placeholder="请输入权限标识符",
                                                            autoComplete="off",
                                                            allowClear=True,
                                                            style={"width": 240},
                                                        ),
                                                        label="权限标识符",
                                                        style={"paddingBottom": "10px"},
                                                    ),
                                                    fac.AntdFormItem(
                                                        fac.AntdSelect(
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
                                                            id="permissions-status-select",
                                                            name="status",
                                                            placeholder="状态",
                                                            style={"width": 240},
                                                        ),
                                                        label="状态",
                                                        style={"paddingBottom": "10px"},
                                                    ),
                                                    fac.AntdFormItem(
                                                        fac.AntdButton(
                                                            "搜索",
                                                            id="permissions-search",
                                                            type="primary",
                                                            icon=fac.AntdIcon(
                                                                icon="antd-search"
                                                            ),
                                                        ),
                                                        style={"paddingBottom": "10px"},
                                                    ),
                                                    fac.AntdFormItem(
                                                        fac.AntdButton(
                                                            "重置",
                                                            id="permissions-reset",
                                                            icon=fac.AntdIcon(
                                                                icon="antd-sync"
                                                            ),
                                                        ),
                                                        style={"paddingBottom": "10px"},
                                                    ),
                                                ],
                                                layout="inline",
                                                id="permissions-search-form",
                                                enableBatchControl=True,
                                            )
                                        ],
                                        hidden=False,
                                    ),
                                )
                            ]
                        ),
                        # fac.AntdRow(
                        #     [
                        #         fac.AntdCol(
                        #             fac.AntdSpace(
                        #                 [
                        #                     fac.AntdButton(
                        #                         [
                        #                             fac.AntdIcon(
                        #                                 icon='antd-plus'
                        #                             ),
                        #                             '新增',
                        #                         ],
                        #                         id={
                        #                             'type': 'notice-operation-button',
                        #                             'index': 'add',
                        #                         },
                        #                         style={
                        #                             'color': '#1890ff',
                        #                             'background': '#e8f4ff',
                        #                             'border-color': '#a3d3ff',
                        #                         },
                        #                     ),
                        #                     fac.AntdButton(
                        #                         [
                        #                             fac.AntdIcon(
                        #                                 icon='antd-edit'
                        #                             ),
                        #                             '修改',
                        #                         ],
                        #                         id={
                        #                             'type': 'notice-operation-button',
                        #                             'index': 'edit',
                        #                         },
                        #                         disabled=True,
                        #                         style={
                        #                             'color': '#71e2a3',
                        #                             'background': '#e7faf0',
                        #                             'border-color': '#d0f5e0',
                        #                         },
                        #                     ),
                        #                     fac.AntdButton(
                        #                         [
                        #                             fac.AntdIcon(
                        #                                 icon='antd-minus'
                        #                             ),
                        #                             '删除',
                        #                         ],
                        #                         id={
                        #                             'type': 'notice-operation-button',
                        #                             'index': 'delete',
                        #                         },
                        #                         disabled=True,
                        #                         style={
                        #                             'color': '#ff9292',
                        #                             'background': '#ffeded',
                        #                             'border-color': '#ffdbdb',
                        #                         },
                        #                     ),
                        #                 ],
                        #                 style={'paddingBottom': '10px'},
                        #             ),
                        #             span=16,
                        #         ),
                        #         fac.AntdCol(
                        #             fac.AntdSpace(
                        #                 [
                        #                     html.Div(
                        #                         fac.AntdTooltip(
                        #                             fac.AntdButton(
                        #                                 [
                        #                                     fac.AntdIcon(
                        #                                         icon='antd-search'
                        #                                     ),
                        #                                 ],
                        #                                 id='notice-hidden',
                        #                                 shape='circle',
                        #                             ),
                        #                             id='notice-hidden-tooltip',
                        #                             title='隐藏搜索',
                        #                         )
                        #                     ),
                        #                     html.Div(
                        #                         fac.AntdTooltip(
                        #                             fac.AntdButton(
                        #                                 [
                        #                                     fac.AntdIcon(
                        #                                         icon='antd-sync'
                        #                                     ),
                        #                                 ],
                        #                                 id='notice-refresh',
                        #                                 shape='circle',
                        #                             ),
                        #                             title='刷新',
                        #                         )
                        #                     ),
                        #                 ],
                        #                 style={
                        #                     'float': 'right',
                        #                     'paddingBottom': '10px',
                        #                 },
                        #             ),
                        #             span=8,
                        #             style={'paddingRight': '10px'},
                        #         ),
                        #     ],
                        #     gutter=5,
                        # ),
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    fac.AntdSpin(
                                        fac.AntdTable(
                                            id="permissions-list-table",
                                            columns=[
                                                {
                                                    "dataIndex": "name",
                                                    "title": "权限名称",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "per_key",
                                                    "title": "权限标识",
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
        # # 新增和编辑通知公告modal
        # fac.AntdModal(
        #     [
        #         fac.AntdForm(
        #             [
        #                 fac.AntdRow(
        #                     [
        #                         fac.AntdCol(
        #                             fac.AntdFormItem(
        #                                 fac.AntdInput(
        #                                     id="notice-notice_title",
        #                                     style={"width": "100%"},
        #                                 ),
        #                                 id="notice-notice_title-form-item",
        #                                 required=True,
        #                                 label="公告标题",
        #                             ),
        #                             span=12,
        #                         ),
        #                         fac.AntdCol(
        #                             fac.AntdFormItem(
        #                                 #                 fac.AntdSelect(
        #                                 #                     options=[
        #                                 #                         {'label': '正常', 'value': 1},
        #                                 #                         {'label': '停用', 'value': 0}
        #                                 #                     ],
        #                                 #                     id='notice-notice_type',
        #                                 #                     style={'width': '100%'},
        #                                 #                 ),
        #                                 #                 id='notice-notice_type-form-item',
        #                                 #                 required=True,
        #                                 #                 label='公告类型',
        #                                 #             ),
        #                                 #             span=12,
        #                                 #         ),
        #                                 #     ],
        #                                 #     gutter=5,
        #                                 # ),
        #                                 # fac.AntdRow(
        #                                 #     [
        #                                 #         fac.AntdCol(
        #                                 #             fac.AntdFormItem(
        #                                 #                 fac.AntdSelect(
        #                                 #                     options=[
        #                                 #                         {'label': '正常', 'value': 1},
        #                                 #                         {'label': '停用', 'value': 0}
        #                                 #                     ],
        #                                 #                     id='notice-status',
        #                                 #                     style={'width': '100%'},
        #                                 #                 ),
        #                                 #                 id='notice-status-form-item',
        #                                 #                 label='状态',
        #                                 #                 labelCol={'span': 3},
        #                                 #                 wrapperCol={'span': 21},
        #                                 #             ),
        #                                 #             span=24,
        #                                 #         ),
        #                                 #     ],
        #                                 #     gutter=5,
        #                                 # ),
        #                                 # fac.AntdRow(
        #                                 #     [
        #                                 #         fac.AntdCol(
        #                                 #             fac.AntdFormItem(
        #                                 #                 fuc.FefferyRichTextEditor(
        #                                 #                     id='notice-content',
        #                                 #                     editorConfig={
        #                                 #                         'placeholder': '请输入...'
        #                                 #                     },
        #                                 #                     uploadImage={
        #                                 #                         # 'server': f'{ApiConfig.BaseUrl}/common/uploadForEditor',
        #                                 #                         'fieldName': 'file',
        #                                 #                         'maxFileSize': 10 * 1024 * 1024,
        #                                 #                         'maxNumberOfFiles': 10,
        #                                 #                         'meta': {
        #                                 #                             # 'base_url': ApiConfig.BaseUrl,
        #                                 #                         },
        #                                 #                         'metaWithUrl': True,
        #                                 #                         'headers': {
        #                                 #                             'Authorization': 'Bearer '
        #                                 #                             # + session.get(
        #                                 #                             #     'Authorization'
        #                                 #                             # )
        #                                 #                         },
        #                                 #                         'withCredentials': True,
        #                                 #                         'timeout': 5 * 1000,
        #                                 #                         'base64LimitSize': 500 * 1024,
        #                                 #                     },
        #                                 #                     uploadVideo={
        #                                 #                         # 'server': f'{ApiConfig.BaseUrl}/common/uploadForEditor',
        #                                 #                         'fieldName': 'file',
        #                                 #                         'maxFileSize': 100
        #                                 #                         * 1024
        #                                 #                         * 1024,
        #                                 #                         'maxNumberOfFiles': 3,
        #                                 #                         'meta': {
        #                                 #                             # 'base_url': ApiConfig.BaseUrl,
        #                                 #                         },
        #                                 #                         'metaWithUrl': True,
        #                                 #                         'headers': {
        #                                 #                             'Authorization': 'Bearer '
        #                                 #                             # + session.get(
        #                                 #                             #     'Authorization'
        #                                 #                             # )
        #                                 #                         },
        #                                 #                         'withCredentials': True,
        #                                 #                         'timeout': 15 * 1000,
        #                                 #                     },
        #                                 #                     editorStyle={
        #                                 #                         'height': 300,
        #                                 #                         'width': '100%',
        #                                 #                     },
        #                                 #                     style={'marginBottom': 15},
        #                                 #                 ),
        #                                 id="notice-notice_content-form-item",
        #                                 label="内容",
        #                                 labelCol={"span": 3},
        #                                 wrapperCol={"span": 21},
        #                             ),
        #                             span=24,
        #                         ),
        #                     ],
        #                     gutter=5,
        #                 ),
        #             ],
        #             labelCol={"span": 6},
        #             wrapperCol={"span": 18},
        #             style={"marginRight": "30px"},
        #         )
        #     ],
        #     id="notice-modal",
        #     mask=False,
        #     width=900,
        #     renderFooter=True,
        #     okClickClose=False,
        # ),
        # # 删除通知公告二次确认modal
        # fac.AntdModal(
        #     fac.AntdText("是否确认删除？", id="notice-delete-text"),
        #     id="notice-delete-confirm-modal",
        #     visible=False,
        #     title="提示",
        #     renderFooter=True,
        #     centered=True,
        # ),
    ]
