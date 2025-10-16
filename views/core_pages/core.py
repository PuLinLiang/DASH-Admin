import re
from dash import html, dcc
import feffery_antd_components as fac
import feffery_utils_components as fuc
from feffery_dash_utils.style_utils import style

from views.core_pages import core_side_menu, personal_info
from config.base_config import BaseConfig
from tools.sys import route_menu

# 令绑定的回调函数子模块生效
import callbacks.core_pages_c  # noqa: F401


def get_page_search_options(current_user):
    """当前模块内工具函数，生成页面搜索选项"""

    options = [{"label": "首页", "value": "/"}]
    for pathname, title in route_menu.routes.items():
        # 忽略已添加的首页
        if pathname in route_menu.index_pathname:
            pass
        elif current_user.is_admin:
            options.append(
                {
                    "label": title,
                    "value": f"{pathname}|{title}",
                }
            )
        # 忽略正则表达式通配页面
        elif isinstance(pathname, re.Pattern):
            pass


        elif (
            # pathname in route_menu.public_pages or  # 公共页面不在搜索范围
            current_user.is_authenticated
            and pathname in getattr(current_user, "role_urls", [])
        ):

            options.append({"label": title, "value": f"{pathname}|{title}"})

    return options


def render(current_pathname, current_user):
    """渲染核心页面骨架

    Args:
        current_user : 当前用户代理对象
        current_pathname (str, optional): 当前页面pathname. Defaults to None.
    """
    # 判断是否需要独立渲染
    if current_pathname in route_menu.independent_pages:
        # 返回不同地址规则对应页面内容
        return route_menu.render_by_url(current_pathname)

    # # 判断是否需要独立通配渲染
    # elif any(
    #     pattern.match(current_pathname)
    #     for pattern in RouterConfig.independent_core_pathnames
    #     if isinstance(pattern, re.Pattern)
    # ):
    #     # 获取命中当前地址的第一个通配规则
    #     match_pattern = None
    #     for pattern in RouterConfig.independent_core_pathnames:
    #         if isinstance(pattern, re.Pattern):
    #             if pattern.match(current_pathname):
    #                 # 更新命中的通配规则
    #                 match_pattern = pattern
    #                 break
    #     # 返回不同地址通配规则对应页面内容
    #     if match_pattern == RouterConfig.wildcard_patterns["独立通配页面演示"]:
    #         return independent_wildcard_page_demo.render(pathname=current_pathname)
    return html.Div(
        [
            # 核心页面常量参数数据
            dcc.Store(
                id="core-page-config",
                data=dict(
                    core_side_width=BaseConfig.core_side_width,
                    core_layout_type=BaseConfig.core_layout_type,
                ),
            ),
            # 核心页面独立路由监听
            dcc.Location(id="core-url", refresh="callback-nav"),
            # 核心页面pathname静默更新
            # dcc.Location(id="core-silently-update-pathname", refresh="callback-nav"),
            # ctrl+k快捷键监听
            fuc.FefferyKeyPress(id="core-ctrl-k-key-press", keys="ctrl.k"),
            # 全屏化切换
            fuc.FefferyFullscreen(
                id="core-fullscreen",
            ),
            # 注入个人信息模态框
            personal_info.render(),
            # 若当前用户角色为系统管理员
            # 页首
            fac.AntdRow(
                [
                    # logo+标题+版本+侧边折叠按钮
                    fac.AntdCol(
                        fac.AntdFlex(
                            [
                                dcc.Link(
                                    fac.AntdSpace(
                                        [
                                            # logo
                                            html.Img(
                                                src="/assets/imgs/logo.svg",
                                                height=32,
                                                style=style(display="block"),
                                            ),
                                            fac.AntdSpace(
                                                [
                                                    # 标题
                                                    fac.AntdText(
                                                        BaseConfig.app_title,
                                                        strong=True,
                                                        style=style(fontSize=15),
                                                    ),
                                                    fac.AntdText(
                                                        BaseConfig.app_version,
                                                        className="global-help-text",
                                                        style=style(fontSize=8),
                                                    ),
                                                ],
                                                align="baseline",
                                                size=3,
                                                id="core-header-title",
                                            ),
                                        ]
                                    ),
                                    href="/",
                                ),
                                # 侧边折叠按钮
                                fac.AntdButton(
                                    fac.AntdIcon(
                                        id="core-side-menu-collapse-button-icon",
                                        icon="antd-menu-fold",
                                        className="global-help-text",
                                    ),
                                    id="core-side-menu-collapse-button",
                                    type="text",
                                    size="small",
                                ),
                            ],
                            id="core-header-side",
                            justify="space-between",
                            align="center",
                            style=style(
                                width=BaseConfig.core_side_width,
                                height="100%",
                                paddingLeft=20,
                                paddingRight=20,
                                borderRight="1px solid #dae0ea",
                                boxSizing="border-box",
                            ),
                        ),
                        flex="none",
                    ),
                    # 页面搜索+功能图标+用户信息
                    fac.AntdCol(
                        fac.AntdFlex(
                            [
                                # 面包屑导航
                                fac.AntdSpace(
                                    [
                                        fac.AntdBreadcrumb(
                                            id='breadcrumb-top',
                                            items=[
                                            ],
                                        ),

                                    ]

                                ),
                                # 页面搜索
                                fac.AntdSpace(
                                    [
                                        fac.AntdSelect(
                                            id="core-page-search",
                                            placeholder="输入关键词搜索页面",
                                            options=get_page_search_options(current_user),
                                            variant="filled",
                                            style=style(width=250),
                                        ),
                                        fac.AntdText(
                                            [
                                                fac.AntdText(
                                                    "Ctrl",
                                                    keyboard=True,
                                                    className="global-help-text",
                                                ),
                                                fac.AntdText(
                                                    "K",
                                                    keyboard=True,
                                                    className="global-help-text",
                                                ),
                                            ]
                                        ),
                                    ],
                                    size=5,
                                    style=style(
                                        **(
                                            {}
                                            if BaseConfig.show_core_page_search
                                            else {"visibility": "hidden"}
                                        )
                                    ),
                                ),
                                # 功能图标+用户信息
                                fac.AntdSpace(
                                    [
                                        # 页面全屏化切换
                                        fac.AntdTooltip(
                                            fac.AntdButton(
                                                id="core-full-screen-toggle-button",
                                                icon=fac.AntdIcon(
                                                    id="core-full-screen-toggle-button-icon",
                                                    icon="antd-full-screen",
                                                    className="global-help-text",
                                                ),
                                                type="text",
                                            ),
                                            title="全屏切换",
                                        ),
                                        # 页面重载
                                        fac.AntdTooltip(
                                            fac.AntdButton(
                                                id="core-reload-button",
                                                icon=fac.AntdIcon(
                                                    icon="antd-reload",
                                                    className="global-help-text",
                                                ),
                                                type="text",
                                                # 省略回调函数的编写
                                                clickExecuteJsString='dash_clientside.set_props("global-reload", { reload: true })',
                                            ),
                                            title="页面重载",
                                        ),
                                        # 示例功能图标
                                        fac.AntdTooltip(
                                            fac.AntdButton(
                                                icon=fac.AntdIcon(
                                                    icon="antd-setting",
                                                    className="global-help-text",
                                                ),
                                                type="text",
                                            ),
                                            title="示例功能图标",
                                        ),
                                        # 示例功能图标
                                        fac.AntdTooltip(
                                            fac.AntdButton(
                                                icon=fac.AntdIcon(
                                                    icon="antd-bell",
                                                    className="global-help-text",
                                                ),
                                                type="text",
                                            ),
                                            title="示例功能图标",
                                        ),
                                        # 示例功能图标
                                        fac.AntdTooltip(
                                            fac.AntdButton(
                                                icon=fac.AntdIcon(
                                                    icon="antd-question-circle",
                                                    className="global-help-text",
                                                ),
                                                type="text",
                                            ),
                                            title="示例功能图标",
                                        ),
                                        # 自定义分隔符
                                        html.Div(
                                            style=style(
                                                width=0,
                                                height=42,
                                                borderLeft="1px solid #e1e5ee",
                                                margin="0 12px",
                                            )
                                        ),
                                        # 用户头像
                                        fac.AntdAvatar(
                                            mode="image",
                                            text="🤩",
                                            size=36,
                                            src=current_user.avatar if current_user.avatar else '/assets/imgs/logo.svg',
                                            style=style(background="#f4f6f9"),
                                        ),
                                        # 用户名+角色
                                        fac.AntdFlex(
                                            [
                                                fac.AntdText(
                                                    f"用户:{current_user.name}",
                                                    strong=True,
                                                ),
                                                fac.AntdText(
                                                    f"岗位：{current_user.post}",
                                                    className="global-help-text",
                                                    style=style(fontSize=12),
                                                ),
                                            ],
                                            vertical=True,
                                        ),
                                        # 用户管理菜单
                                        fac.AntdDropdown(
                                            fac.AntdButton(
                                                icon=fac.AntdIcon(
                                                    icon="antd-more",
                                                    className="global-help-text",
                                                ),
                                                type="text",
                                            ),
                                            id="core-pages-header-user-dropdown",
                                            menuItems=[
                                                {
                                                    "title": "个人信息",
                                                    "key": "个人信息",
                                                },
                                                # 若当前用户角色为系统管理员
                                                {"isDivider": True},
                                                {
                                                    "title": "退出登录",
                                                    "href": "/logout",
                                                },
                                            ],
                                            trigger="click",
                                        ),
                                    ]
                                ),
                            ],
                            justify="space-between",
                            align="center",
                            style=style(
                                height="100%",
                                paddingLeft=20,
                                paddingRight=20,
                            ),
                        ),
                        flex="auto",
                    ),
                ],
                wrap=False,
                align="middle",
                style=style(
                    height=72,
                    borderBottom="1px solid #dae0ea",
                    position="sticky",
                    top=0,
                    zIndex=1000,
                    background="#fff",
                ),
            ),
            # 主题区域
            fac.AntdRow(
                [
                    # 侧边栏
                    fac.AntdCol(
                        core_side_menu.render(
                            current_user=current_user),),
                    # 内容区域
                    fac.AntdCol(
                        # 根据页面呈现类型，渲染具有相同id的页面挂载目标组件
                        (
                            # 单页面形式
                            fac.AntdSkeleton(
                                html.Div(
                                    id="core-container",
                                    style=style(padding="36px 42px"),
                                ),
                                listenPropsMode="include",
                                includeProps=["core-container.children"],
                                active=True,
                                style=style(padding="36px 42px"),
                            )
                            if BaseConfig.core_layout_type == "single"
                            # 多标签页形式
                            else fac.AntdTabs(
                                id="core-container",
                                items=[],
                                type="editable-card",
                                size="small",
                                style=style(padding="6px 12px"),
                            )
                        ),
                        flex="auto",
                    ),
                ],
                wrap=False,
            ),
        ]
    )
