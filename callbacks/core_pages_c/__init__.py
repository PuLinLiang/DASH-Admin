import time
import dash
from dash import set_props, Patch, dcc
from dash.dependencies import Input, Output, State, ClientsideFunction

from server import app, current_user,route_menu
from views.status_pages import _404


# 路由配置参数


# 令绑定的回调函数子模块生效
app.clientside_callback(
    # 控制核心页面侧边栏折叠
    ClientsideFunction(
        namespace="clientside_basic", function_name="handleSideCollapse"
    ),
    [
        Output("core-side-menu-collapse-button-icon", "icon"),
        Output("core-header-side", "style"),
        Output("core-header-title", "style"),
        Output("core-side-menu-affix", "style"),
        Output("core-side-menu", "inlineCollapsed"),
    ],
    Input("core-side-menu-collapse-button", "nClicks"),
    [
        State("core-side-menu-collapse-button-icon", "icon"),
        State("core-header-side", "style"),
        State("core-page-config", "data"),
    ],
    prevent_initial_call=True,
)

app.clientside_callback(
    # 控制页首页面搜索切换功能
    ClientsideFunction(
        namespace="clientside_basic", function_name="handleCorePageSearch"
    ),
    Input("core-page-search", "value"),
)

app.clientside_callback(
    # 控制ctrl+k快捷键聚焦页面搜索框
    ClientsideFunction(
        namespace="clientside_basic", function_name="handleCorePageSearchFocus"
    ),
    # 其中更新key用于强制刷新状态
    [
        Output("core-page-search", "autoFocus"),
        Output("core-page-search", "key"),
    ],
    Input("core-ctrl-k-key-press", "pressedCounts"),
    prevent_initial_call=True,
)


@app.callback(
    Input("core-pages-header-user-dropdown", "nClicks"),
    State("core-pages-header-user-dropdown", "clickedKey"),
)
def open_user_manage_drawer(nClicks, clickedKey):
    """打开个人信息、用户管理面板"""

    if clickedKey == "个人信息":
        set_props("personal-info-modal", {"visible": True, "loading": True})

@app.callback(
    [
        Output("core-container", "children"),
        Output("core-container", "items"),
        Output("core-container", "activeKey"),
        Output("core-side-menu", "currentKey"),
        Output("core-side-menu", "openKeys"),
        Output("core-url", "pathname"),
        Output("breadcrumb-top", "items"),  # 面包屑同步
    ],
    [Input("core-url", "pathname"), Input("core-container", "activeKey")],
    [
        State("core-container", "itemKeys"),
        State("core-page-config", "data"),
    ],
)
def core_router(
    pathname,
    tabs_active_key,
    tabs_item_keys,
    page_config,
):
    """核心页面路由控制及侧边菜单同步"""
    # 统一首页pathname
    if pathname == route_menu.index_pathname:
        pathname = "/"
    # 若当前目标pathname不是有效路由
    if pathname not in route_menu.routes.keys():
        return _404.render(),dash.no_update, pathname,dash.no_update,dash.no_update,pathname,dash.no_update
    if pathname not in current_user.role_urls:
            # 首页不受权限控制影响
            if pathname not in route_menu.index_pathname:
                # 重定向至_403页面
                set_props(
                    "global-redirect",
                    {
                        "children": dcc.Location(
                            pathname="/403-demo", id="global-redirect"
                        )
                    },
                )
                return dash.no_update
    # 仅单页面形式下为骨架屏动画添加额外效果持续时间
    if page_config["core_layout_type"] == "single":
        # 增加一点加载动画延迟^_^
        time.sleep(0.5)
    # 核心渲染页面
    page_content = route_menu.render_by_url(pathname,current_user=current_user)

    # 多标签页形式
    if page_config.get("core_layout_type") == "tabs":
        # 基于Patch进行标签页子项远程映射更新
        p = Patch()

        tabs_item_keys = tabs_item_keys or []

        # 若标签页子项此前为空，即初始化加载
        if not tabs_item_keys:
            # 根据当前目标标签页，处理标签页子项的追加操作
            if pathname in route_menu.index_pathname:
                p.append(
                    {
                        "label": "首页",
                        "key": "/",
                        "children": route_menu.render_by_url("/"),

                        "closable": False,
                        "contextMenu": [
                            {"key": key, "label": key}
                            for key in ["关闭其他", "刷新页面"]
                        ],
                    }
                )
            else:
                p.extend(
                    [
                        {
                            "label": "首页",
                            "key": "/",
                            "children": route_menu.render_by_url("/"),
                            "closable": False,
                            "contextMenu": [
                                {"key": key, "label": key}
                                for key in ["关闭其他", "刷新页面"]
                            ],
                        },
                        {
                            "label": route_menu.routes[pathname],
                            "key": pathname,
                            "children": page_content,
                            "contextMenu": [
                                {"key": key, "label": key}
                                for key in [
                                    "关闭当前",
                                    "关闭其他",
                                    "关闭所有",
                                    "刷新页面",
                                ]
                            ],
                        },
                    ]
                )

            next_active_key = pathname
            next_current_key = pathname
            next_pathname = pathname

        # 若标签页子项此前不为空，即用户手动切换标签页
        else:
            next_active_key = dash.no_update
            next_current_key = tabs_active_key
            next_pathname = tabs_active_key

            if dash.ctx.triggered_id == "core-url":
                if pathname not in tabs_item_keys:
                    p.append(
                        {
                            "label": route_menu.routes[pathname],
                            "key": pathname,
                            "children": page_content,
                            "contextMenu": [
                                {"key": key, "label": key}
                                for key in [
                                    "关闭当前",
                                    "关闭其他",
                                    "关闭所有",
                                    "刷新页面",
                                ]
                            ],
                        }
                    )
                    next_active_key = pathname
                    next_current_key = pathname
                    next_pathname = pathname
                else:
                    next_active_key = pathname
                    next_current_key = dash.no_update
                    next_pathname = pathname
        # 获取当前程 面包屑导航
        breadcrumb_items = route_menu.get_breadcrumb(pathname)
        # 获取当前地址的 子菜单展开父菜单"" 的key
        menu_open_keys = route_menu.get_open_keys(pathname)
        return [
            # 当前模式下不操作children
            dash.no_update,
            p,
            next_active_key,
            next_current_key,
            menu_open_keys,
            # 静默更新pathname
            next_pathname,
            breadcrumb_items,
        ]
    # 面包屑
    breadcrumb_items = route_menu.get_breadcrumb(pathname)
    # 子菜单展开父菜单"" 的key
    menu_open_keys = route_menu.get_open_keys(pathname)

    # 单页面形式
    return [
        page_content,
        # 当前模式下不操作items
        dash.no_update,
        # 当前模式下不操作activeKey
        dash.no_update,
        pathname,
        menu_open_keys,
        # 当前模式下不操作pathname
        pathname,
        breadcrumb_items,
    ]


app.clientside_callback(
    ClientsideFunction(
        namespace="clientside_basic", function_name="handleCoreTabsClose"
    ),
    [
        Output("core-container", "items", allow_duplicate=True),
        Output("core-container", "activeKey", allow_duplicate=True),
    ],
    [
        Input("core-container", "tabCloseCounts"),
        Input("core-container", "clickedContextMenu"),
    ],
    [State("core-container", "latestDeletePane"), State("core-container", "items")],
    prevent_initial_call=True,
)

app.clientside_callback(
    ClientsideFunction(
        namespace="clientside_basic", function_name="handleCoreFullscreenToggle"
    ),
    [
        Output("core-fullscreen", "isFullscreen"),
        Output("core-full-screen-toggle-button-icon", "icon"),
    ],
    [
        Input("core-full-screen-toggle-button", "nClicks"),
        Input("core-fullscreen", "isFullscreen"),
    ],
    State("core-full-screen-toggle-button-icon", "icon"),
    prevent_initial_call=True,
)
