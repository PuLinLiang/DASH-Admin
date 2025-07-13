import feffery_antd_components as fac
from dash import html
from tools.pubilc.enum import LogModule, OperationType
from callbacks.system_c import sys_log_c


def render(*args, **kwargs):
    return [
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
                                                        # 日志等级搜索选择框
                                                        fac.AntdSelect(
                                                            id="log-logmodule-select",
                                                            name="logmodule",
                                                            options=[
                                                                {
                                                                    "label": log.description,
                                                                    "value": log.code,
                                                                }
                                                                for log in LogModule
                                                            ],
                                                            placeholder="用户状态",
                                                            style={"width": 200},
                                                        ),
                                                        label="日志模块",
                                                    ),
                                                    fac.AntdFormItem(
                                                        # 日志等级搜索选择框
                                                        fac.AntdSelect(
                                                            id="log-operation-select",
                                                            name="operation",
                                                            options=[
                                                                {
                                                                    "label": op.description,
                                                                    "value": op.code,
                                                                }
                                                                for op in OperationType
                                                            ],
                                                            placeholder="用户状态",
                                                            style={"width": 200},
                                                        ),
                                                        label="操作类型",
                                                    ),
                                                    fac.AntdFormItem(
                                                        # 日志等级搜索选择框
                                                        fac.AntdSelect(
                                                            id="log-level-select",
                                                            name="log_level",
                                                            options=[
                                                                {
                                                                    "label": "正常",
                                                                    "value": "INFO",
                                                                },
                                                                {
                                                                    "label": "错误",
                                                                    "value": "ERROR",
                                                                },
                                                                {
                                                                    "label": "警告",
                                                                    "value": "WARNING",
                                                                },
                                                                {
                                                                    "label": "调试",
                                                                    "value": "DEBUG",
                                                                },
                                                            ],
                                                            placeholder="用户状态",
                                                            style={"width": 200},
                                                        ),
                                                        label="日志等级",
                                                    ),
                                                    fac.AntdFormItem(
                                                        fac.AntdDateRangePicker(
                                                            id="log_create_time-range",
                                                            name="create_time_range",
                                                            showTime=True,
                                                            needConfirm=True,
                                                            style={"width": 200},
                                                        ),
                                                        label="时间范围",
                                                    ),
                                                    fac.AntdFormItem(
                                                        fac.AntdButton(
                                                            "搜索",
                                                            id="log-search",
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
                                                            id="log-reset",
                                                            icon=fac.AntdIcon(
                                                                icon="antd-sync"
                                                            ),
                                                        ),
                                                        style={"paddingBottom": "10px"},
                                                    ),
                                                ],
                                                layout="inline",
                                                id="log-search-form",
                                                enableBatchControl=True,
                                            )
                                        ],
                                        hidden=False,
                                    ),
                                )
                            ]
                        ),
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    fac.AntdSpin(
                                        fac.AntdTable(
                                            id="log-list-table",
                                            columns=[
                                                {
                                                    "dataIndex": "timestamp",
                                                    "title": "时间",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "log_level",
                                                    "title": "等级",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "message",
                                                    "title": "内容",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "logmodule",
                                                    "title": "模块",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "operation",
                                                    "title": "操作",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "logmodule_operation",
                                                    "title": "操作详情",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "status",
                                                    "title": "状态",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                {
                                                    "dataIndex": "duration_ms",
                                                    "title": "耗时",
                                                    "renderOptions": {
                                                        "renderType": "ellipsis"
                                                    },
                                                },
                                                # {
                                                #     "dataIndex": "ip",
                                                #     "title": "IP",
                                                #     "renderOptions": {
                                                #         "renderType": "ellipsis"
                                                #     },
                                                # },
                                                {
                                                    "dataIndex": "description",
                                                    "title": "额外信息",
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
    ]
